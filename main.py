# main.py

# =================================================================================
# 1. IMPORT LIBRARIES
# =================================================================================
from flask import Flask
from threading import Thread
import gspread
from google.oauth2.service_account import Credentials
import discord
from discord.ext import tasks
import os
from dotenv import load_dotenv
from thefuzz import process
import datetime
import pytz
import json
# Load environment variables from a .env file for local development
load_dotenv()

# =================================================================================
# 2. BOT & SERVER CONFIGURATION (LOADED FROM ENVIRONMENT)
# =================================================================================
TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = int(os.getenv("SERVER_ID", 0))
DRAFT_CHANNEL_ID = int(os.getenv("DRAFT_CHANNEL_ID", 0))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# =================================================================================
# 3. GOOGLE SHEETS & LEAGUE CONFIGURATION
# =================================================================================
TEAMS_PER_LEAGUE = 10

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds_json_str = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json_str)
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
gclient = gspread.authorize(creds)

SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
sheet = gclient.open_by_key(SHEET_ID)
draft_board_sheet = sheet.sheet1
player_sheet = sheet.get_worksheet(1)

# =================================================================================
# 4. HELPER FUNCTIONS
# =================================================================================
def get_id_from_mention(mention: str) -> int:
    try:
        return int(mention.strip('<@!>'))
    except (ValueError, TypeError):
        return 0

def get_mention_from_id(user_id: int) -> str:
    return f"<@{user_id}>"

# =================================================================================
# 5. GLOBAL DRAFT STATE VARIABLES
# =================================================================================
row = 5
prow = 0
col = 4
pcol = 0
picknum = 1
tradecount = 0
drafted = []
draft_order_mentions = []
player_dict = {}

# --- PINGER STATE VARIABLES ---
current_picker_id = None
pick_start_time = None
pings_sent = 0
# -----------------------------

# =================================================================================
# 6. LOAD PLAYER & DRAFT ORDER DATA
# =================================================================================
print("Loading player data from Google Sheet...")
qbs = player_sheet.col_values(3)[3:]
rbs = player_sheet.col_values(8)[3:]
wrs = player_sheet.col_values(13)[3:]
tes = player_sheet.col_values(18)[3:]
all_players_original = qbs + rbs + wrs + tes

player_dict = {name.upper(): name for name in all_players_original if name}
print(f"Loaded {len(player_dict)} players.")


DRAFT_MANAGER_IDS = []
manager_ids_str = os.getenv("DRAFT_MANAGER_IDS")
if manager_ids_str:
    try:
        DRAFT_MANAGER_IDS = [int(id_str) for id_str in manager_ids_str.split(',')]
    except ValueError:
        print("ERROR: Could not parse DRAFT_MANAGER_IDS from .env file.")
else:
    print("ERROR: DRAFT_MANAGER_IDS not found in .env file.")

initial_draft_order = [get_mention_from_id(id) for id in DRAFT_MANAGER_IDS]

reversed_order = initial_draft_order[::-1]
full_draft_order = []
for i in range(16):
    if i % 2 == 0:
        full_draft_order.extend(initial_draft_order)
    else:
        full_draft_order.extend(reversed_order)

# =================================================================================
# 7. DISCORD BOT EVENTS & TASKS
# =================================================================================
@tasks.loop(minutes=5)
async def check_for_slow_drafter():
    global pings_sent, pick_start_time
    if current_picker_id is None or pick_start_time is None:
        return

    desired_tz = pytz.timezone('America/Los_Angeles')
    now = datetime.datetime.now(desired_tz)

    is_quiet_now = 0 <= now.hour < 7
    pick_started_during_quiet = 0 <= pick_start_time.astimezone(desired_tz).hour < 7

    if pick_started_during_quiet and not is_quiet_now:
        seven_am_today = now.replace(hour=7, minute=0, second=0, microsecond=0)
        pick_start_time = seven_am_today
        pings_sent = 0

    if is_quiet_now:
        return

    time_since_pick_started = now - pick_start_time.astimezone(desired_tz)
    hours_passed = time_since_pick_started.total_seconds() / 3600
    intervals_passed = int(hours_passed // 2)

    if intervals_passed > pings_sent:
        channel = client.get_channel(DRAFT_CHANNEL_ID)
        if not channel: return

        if pings_sent < 3:
            pings_sent += 1
            await channel.send(f"⏰ Reminder! {get_mention_from_id(current_picker_id)}, you are on the clock. It has been over {pings_sent * 2} hours.")
        elif pings_sent == 3:
            pings_sent += 1
            await channel.send(f"🚨 **FINAL WARNING!** {get_mention_from_id(current_picker_id)}, you are on the clock and have been reminded multiple times. Please make your pick soon or a decision may be made by the commissioner.")

@client.event
async def on_ready():
    await client.wait_until_ready()
    print(f'Bot is ready and has logged in as {client.user}')
    check_for_slow_drafter.start()
    channel = client.get_channel(DRAFT_CHANNEL_ID)
    if not channel:
        print(f"ERROR: Could not find channel with ID {DRAFT_CHANNEL_ID}.")
        return
    await channel.send("!restart")

@client.event
async def on_guild_join(guild):
    intro_message = """
👋 Ayo, what's poppin', crew? It's your boy J'Dinkalage Morgoone, straight outta Boomin' U, holdin' it down in these streets.

I'm finna run this weak-ass draft, trackin' y'all's janky picks and slappin' 'em into the Google Sheet on straight auto, no cap, fam.

**COMMANDS FOR ALL MY DAWGS:**

Listen up, ‘specially if you was dodgin’ class with more teachers than homies or rollin' up in that short bus. Y’all better lock in for these commands when we draftin’:

`!draft [Player Name]`
This how you snatch your player, fam. Spell it like you illiterate, it’s cool—bot got that fuzzy matchin’ to scoop the right dude.
*Example: `!draft christian mcafferey` still gonna bang, no stress.*

`!change [Player Name]`
Fucked up your pick? Use this to flip your last pick, but you only got a hot minute ‘fore the next homie picks. Move quick, bruh.

`!trade @UserA [picks] for @UserB [picks]`
This for when you slangin’ them future picks. Bot’s gonna log that shit and remix the draft order on the fly.
*Example: `!trade @Steve 25 51 for @Brenda 30`—you know the vibes.*

`!whopick`
Tells you who’s holdin’ up the line, ‘cause some of y’all be movin’ like molasses.

`!ovr`
Gives you the total pick count in this draft, keepin’ shit real.

`!help`
Hit this when you lost as fuck and need the rundown again. Ain’t no shame, fam.

AND with the number 1 pick... Vinny selects...
"""
    target_channel = None
    for channel in guild.text_channels:
        if "general" in channel.name.lower() or "bot" in channel.name.lower():
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    if not target_channel:
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                target_channel = channel
                break
    if target_channel:
        await target_channel.send(intro_message)
    else:
        print(f"Could not find a suitable channel to post welcome message in guild {guild.name}.")
        
@client.event
async def on_message(message):
    global row, col, picknum, drafted, draft_order_mentions, prow, pcol, tradecount
    global current_picker_id, pick_start_time, pings_sent
    
    if message.author == client.user or not message.content: return

    parts = message.content.split()
    command = parts[0].lower()
    start_col = 4
    end_col = start_col + TEAMS_PER_LEAGUE - 1

    def find_player(query: str, is_change_command: bool = False):
        query_upper = query.upper()
        if is_change_command:
            last_pick_upper = drafted[-1]
            available_players = [name for name in player_dict.keys() if name not in drafted or name == last_pick_upper]
        else:
            available_players = [name for name in player_dict.keys() if name not in drafted]
        if not available_players: return None
        best_match = process.extractOne(query_upper, available_players)
        if best_match and best_match[1] > 85:
            return player_dict[best_match[0]]
        return None

    if command == "!restart":
        await message.channel.send("🔄 Relaunching and syncing with the Google Sheet...")
        try:
            picknum = int(draft_board_sheet.cell(3, 17).value)
            drafted_from_sheet = draft_board_sheet.col_values(18)[2:]
            drafted = [x.upper() for x in drafted_from_sheet if x]
            draft_order_mentions = draft_board_sheet.col_values(20)[2:]
            tradecount = len(draft_board_sheet.col_values(19)[2:])

            if picknum > 1:
                picks_done = picknum - 1
                row = 5 + (picks_done // TEAMS_PER_LEAGUE)
                pick_in_round = picks_done % TEAMS_PER_LEAGUE
                if (row - 5) % 2 == 0: col = start_col + pick_in_round
                else: col = end_col - pick_in_round
            else: row, col = 5, 4
            if picknum > 1:
                prev_pick_num = picknum - 2
                prow = 5 + (prev_pick_num // TEAMS_PER_LEAGUE)
                prev_pick_in_round = prev_pick_num % TEAMS_PER_LEAGUE
                if (prow - 5) % 2 == 0: pcol = start_col + prev_pick_in_round
                else: pcol = end_col - prev_pick_in_round
            else: prow, pcol = 0, 0

            total_picks = TEAMS_PER_LEAGUE * 16
            if picknum <= total_picks:
                on_the_clock = draft_order_mentions[picknum - 1]
                current_picker_id = get_id_from_mention(on_the_clock)
                pick_start_time = datetime.datetime.now(pytz.utc)
                pings_sent = 0
            
            await message.channel.send(f"✅ Relaunch complete. We are at pick **#{picknum}**.")
            round_num = ((picknum - 1) // TEAMS_PER_LEAGUE) + 1
            pick_in_round_disp = ((picknum - 1) % TEAMS_PER_LEAGUE) + 1
            await message.channel.send(f"It is **Round {round_num}, Pick {pick_in_round_disp}**. {draft_order_mentions[picknum - 1]}, you are on the clock!")
        except Exception as e:
            await message.channel.send(f"⚠️ **Error during restart:** {e}\nPlease ensure the Google Sheet format is correct.")

    elif command == "!help":
        help_message = """
Hello! I'm the draft bot. Here are my commands:
`!draft [Player Name]`: Make your draft pick (typos are okay!). *e.g., !draft Christian McCafferey*
`!change [Player Name]`: Change your most recent pick.
`!trade @UserA [picks] for @UserB [picks]`: Log a trade.
`!whopick`: Shows who is currently on the clock.
`!ovr`: Shows the current overall pick number.
`!restart`: Resyncs the bot with the spreadsheet.
        """
        await message.channel.send(help_message)

    elif command == "!draft":
        if len(parts) < 2: return
        on_the_clock_id = get_id_from_mention(draft_order_mentions[picknum - 1])
        if message.author.id != on_the_clock_id:
            await message.channel.send(f"Hold on, it's not your turn! We're waiting on {draft_order_mentions[picknum - 1]}.")
            return
        
        player_query = " ".join(parts[1:])
        official_name = find_player(player_query)
        if official_name:
            draft_board_sheet.update_cell(row, col, official_name)
            draft_board_sheet.update_cell(picknum + 2, 18, official_name)
            draft_board_sheet.update_cell(3, 17, picknum + 1)
            drafted.append(official_name.upper())
            
            round_num = ((picknum - 1) // TEAMS_PER_LEAGUE) + 1
            pick_in_round = ((picknum - 1) % TEAMS_PER_LEAGUE) + 1
            await message.channel.send(f"**R{round_num}.{pick_in_round} (#__{picknum}__):** {message.author.mention} selects **{official_name}**!")
            
            prow, pcol = row, col
            picknum += 1
            
            total_picks = TEAMS_PER_LEAGUE * 16
            if picknum > total_picks:
                ending_message = """
----------------------------------------------------
🎉 **THE DRAFT IS OFFICIALLY COMPLETE!** 🎉
----------------------------------------------------

Yo, the last pick just dropped! Big ups to y'all for crushin' this draft, fam!

Now the real game pops off. Time to scope them rosters, snatch up them waiver wire steals, and get ready to clown in Week 1.

May the fantasy gods keep it 💯 and bless your squad. Good luck, homies! 🏆😎
"""
                await message.channel.send(ending_message)
                current_picker_id = None
                pick_start_time = None
                pings_sent = 0
                check_for_slow_drafter.stop()
                return
                
            picks_done = picknum - 1
            row = 5 + (picks_done // TEAMS_PER_LEAGUE)
            pick_in_round_next = picks_done % TEAMS_PER_LEAGUE
            if (row - 5) % 2 == 0: col = start_col + pick_in_round_next
            else: col = end_col - pick_in_round_next
            
            round_num_next = ((picknum - 1) // TEAMS_PER_LEAGUE) + 1
            pick_in_round_next_disp = ((picknum - 1) % TEAMS_PER_LEAGUE) + 1
            on_the_clock_next = draft_order_mentions[picknum - 1]
            
            current_picker_id = get_id_from_mention(on_the_clock_next)
            pick_start_time = datetime.datetime.now(pytz.utc)
            pings_sent = 0
            
            await message.channel.send(f"Next up: **Round {round_num_next}, Pick {pick_in_round_next_disp}**. {on_the_clock_next}, you're on the clock!")
        else:
            await message.channel.send(f"Invalid pick. I can't find **{player_query}** in the player list.")

    elif command == "!change":
        if len(parts) < 2: return
        if picknum <= 1: return
        last_picker_id = get_id_from_mention(draft_order_mentions[picknum - 2])
        if message.author.id != last_picker_id:
            await message.channel.send("Error: You can only change your own most recent pick.")
            return

        player_query = " ".join(parts[1:])
        new_official_name = find_player(player_query, is_change_command=True)
        if new_official_name:
            old_official_name = player_dict[drafted[-1]]
            drafted[-1] = new_official_name.upper()
            draft_board_sheet.update_cell(prow, pcol, new_official_name)
            draft_board_sheet.update_cell(picknum, 18, new_official_name)
            await message.channel.send(f"✅ **Pick Changed!** {message.author.mention} has updated their pick from **{old_official_name}** to **{new_official_name}**.")
            on_the_clock = draft_order_mentions[picknum - 1]
            await message.channel.send(f"The clock has not advanced. {on_the_clock}, you are still on the clock.")
        else:
            await message.channel.send(f"Invalid pick. I can't find **{player_query}** in the player list or that player has already been drafted by someone else.")

    elif command == "!trade":
        try:
            msg_content = message.content
            if ' for ' not in msg_content:
                await message.channel.send("Invalid trade format. Use: `!trade @UserA [picks] for @UserB [picks]`")
                return

            parts = msg_content.split(' for ')
            part1 = parts[0].split()
            part2 = parts[1].split()
            user_a_mention = part1[1]
            user_a_id = get_id_from_mention(user_a_mention)
            user_a_picks = [int(p) for p in part1[2:]]
            user_b_mention = part2[0]
            user_b_id = get_id_from_mention(user_b_mention)
            user_b_picks = [int(p) for p in part2[1:]]

            for p in user_a_picks + user_b_picks:
                if p < picknum:
                    await message.channel.send(f"Error: Pick #{p} has already occurred.")
                    return
            for p in user_a_picks:
                if get_id_from_mention(draft_order_mentions[p-1]) != user_a_id:
                    await message.channel.send(f"Verification failed: {user_a_mention} does not own pick #{p}.")
                    return
            for p in user_b_picks:
                if get_id_from_mention(draft_order_mentions[p-1]) != user_b_id:
                    await message.channel.send(f"Verification failed: {user_b_mention} does not own pick #{p}.")
                    return

            for p in user_a_picks:
                draft_order_mentions[p-1] = user_b_mention
            for p in user_b_picks:
                draft_order_mentions[p-1] = user_a_mention

            trade_log_msg = message.content.replace("!trade ", "")
            draft_board_sheet.update_cell(3 + tradecount, 19, trade_log_msg)
            tradecount += 1
            temp_draft_data = [[pick] for pick in draft_order_mentions]
            draft_board_sheet.update(f"T3:T{len(temp_draft_data)+2}", temp_draft_data)
            
            on_the_clock = draft_order_mentions[picknum - 1]
            if get_id_from_mention(on_the_clock) != current_picker_id:
                current_picker_id = get_id_from_mention(on_the_clock)
                pick_start_time = datetime.datetime.now(pytz.utc)
                pings_sent = 0
            
            await message.channel.send(f"🤝 **Trade Confirmed!** The draft order has been updated. {on_the_clock} is now on the clock.")
        except (ValueError, IndexError):
            await message.channel.send("Invalid trade format or pick number.")

    elif command == "!whopick":
        on_the_clock = draft_order_mentions[picknum - 1]
        await message.channel.send(f"{on_the_clock} is currently on the clock for pick #{picknum}.")
    
    elif command == "!ovr":
        await message.channel.send(f"The current overall pick is **#{picknum}**.")

# =================================================================================
# 9. WEB SERVER FOR RENDER HEALTH CHECKS
# =================================================================================
app = Flask('')
@app.route('/')
def home():
    return "I am alive!"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = Thread(name='Thread', target=run)
    t.start()

# =================================================================================
# 8. RUN THE BOT
# =================================================================================
if TOKEN and SERVER_ID and SHEET_ID and DRAFT_CHANNEL_ID and DRAFT_MANAGER_IDS:
    keep_alive()
    client.run(TOKEN)
else:
    print("ERROR: One or more required environment variables are missing or invalid.")