"""
update_sheets.py — FIXED version. Updates Google Sheet for 2026 season.
Run: python3 update_sheets.py
"""

import json
import os
import sys
import time
from dotenv import load_dotenv
import gspread
from google.oauth2.service_account import Credentials

load_dotenv()

# ── 2026 PLAYER RANKINGS (teams verified for August 2026) ─────────────────

QBS = [
    (1, "Josh Allen", "BUF"), (2, "Lamar Jackson", "BAL"),
    (3, "Drake Maye", "NE"), (4, "Jalen Hurts", "PHI"),
    (5, "Joe Burrow", "CIN"), (6, "Caleb Williams", "CHI"),
    (7, "Jayden Daniels", "WAS"), (8, "Justin Herbert", "LAC"),
    (9, "Dak Prescott", "DAL"), (10, "Jaxson Dart", "NYG"),
    (11, "Trevor Lawrence", "JAC"), (12, "Bo Nix", "DEN"),
    (13, "Brock Purdy", "SF"), (14, "Patrick Mahomes", "KC"),
    (15, "Matthew Stafford", "LAR"), (16, "Kyler Murray", "MIN"),
    (17, "Jared Goff", "DET"), (18, "Baker Mayfield", "TB"),
    (19, "Tyler Shough", "NO"), (20, "Jordan Love", "GB"),
    (21, "Malik Willis", "MIA"), (22, "Daniel Jones", "IND"),
    (23, "Cam Ward", "TEN"), (24, "C.J. Stroud", "HOU"),
    (25, "Sam Darnold", "SEA"), (26, "Jacoby Brissett", "ARI"),
    (27, "Bryce Young", "CAR"), (28, "Fernando Mendoza", "LV"),
    (29, "Aaron Rodgers", "PIT"), (30, "Deshaun Watson", "CLE"),
    (31, "Geno Smith", "NYJ"), (32, "Tua Tagovailoa", "ATL"),
    (33, "Shedeur Sanders", "CLE"), (34, "Michael Penix Jr.", "ATL"),
    (35, "Kirk Cousins", "LV"), (36, "J.J. McCarthy", "MIN"),
]

RBS = [
    (1, "Jahmyr Gibbs", "DET"), (2, "Bijan Robinson", "ATL"),
    (3, "Christian McCaffrey", "SF"), (4, "Jonathan Taylor", "IND"),
    (5, "James Cook", "BUF"), (6, "De'Von Achane", "MIA"),
    (7, "Ashton Jeanty", "LV"), (8, "Chase Brown", "CIN"),
    (9, "Derrick Henry", "BAL"), (10, "Omarion Hampton", "LAC"),
    (11, "Saquon Barkley", "PHI"), (12, "Kenneth Walker III", "KC"),
    (13, "Kyren Williams", "LAR"), (14, "Breece Hall", "NYJ"),
    (15, "Javonte Williams", "DAL"), (16, "Jeremiyah Love", "ARI"),
    (17, "Josh Jacobs", "GB"), (18, "Cam Skattebo", "NYG"),
    (19, "Travis Etienne", "NO"), (20, "Quinshon Judkins", "CLE"),
    (21, "David Montgomery", "HOU"), (22, "TreVeyon Henderson", "NE"),
    (23, "D'Andre Swift", "CHI"), (24, "Bhayshul Tuten", "JAC"),
    (25, "Jadarian Price", "SEA"), (26, "Rhamondre Stevenson", "NE"),
    (27, "Bucky Irving", "TB"), (28, "Tony Pollard", "TEN"),
    (29, "Chuba Hubbard", "CAR"), (30, "Jaylen Warren", "PIT"),
    (31, "Rico Dowdle", "PIT"), (32, "Kenneth Gainwell", "TB"),
    (33, "RJ Harvey", "DEN"), (34, "Kyle Monangai", "CHI"),
    (35, "Aaron Jones", "MIN"), (36, "J.K. Dobbins", "DEN"),
    (37, "Blake Corum", "LAR"), (38, "Rachaad White", "WAS"),
    (39, "Jacory Croskey-Merritt", "WAS"), (40, "Jordan Mason", "MIN"),
    (41, "Jonathon Brooks", "CAR"), (42, "Chris Rodriguez Jr.", "JAC"),
    (43, "Woody Marks", "HOU"), (44, "Tyrone Tracy Jr.", "NYG"),
    (45, "Isiah Pacheco", "DET"), (46, "Alvin Kamara", "NO"),
    (47, "Tyler Allgeier", "ARI"), (48, "Emanuel Wilson", "SEA"),
    (49, "Justice Hill", "BAL"), (50, "Zach Charbonnet", "SEA"),
    (51, "Jaylen Wright", "MIA"), (52, "Trey Benson", "ARI"),
    (53, "Tyjae Spears", "TEN"), (54, "Brian Robinson", "WAS"),
    (55, "Gus Edwards", "LAC"), (56, "Ezekiel Elliott", "DAL"),
    (57, "Jerome Ford", "CLE"), (58, "Kendre Miller", "NO"),
    (59, "Antonio Gibson", "NE"), (60, "Jaleel McLaughlin", "DEN"),
    (61, "Roschon Johnson", "CHI"), (62, "Khalil Herbert", "CHI"),
    (63, "Dameon Pierce", "HOU"), (64, "Keaton Mitchell", "BAL"),
    (65, "Clyde Edwards-Helaire", "KC"), (66, "Alexander Mattison", "LV"),
    (67, "Tank Bigsby", "JAC"), (68, "Will Shipley", "PHI"),
    (69, "D'Onta Foreman", "CLE"), (70, "Dylan Laube", "LV"),
    (71, "AJ Dillon", "GB"), (72, "Jordan Mason", "SF"),
]

WRS = [
    (1, "Puka Nacua", "LAR"), (2, "Ja'Marr Chase", "CIN"),
    (3, "Jaxon Smith-Njigba", "SEA"), (4, "Amon-Ra St. Brown", "DET"),
    (5, "CeeDee Lamb", "DAL"), (6, "Justin Jefferson", "MIN"),
    (7, "Malik Nabers", "NYG"), (8, "Nico Collins", "HOU"),
    (9, "George Pickens", "DAL"), (10, "Drake London", "ATL"),
    (11, "A.J. Brown", "NE"), (12, "Garrett Wilson", "NYJ"),
    (13, "Chris Olave", "NO"), (14, "Zay Flowers", "BAL"),
    (15, "Tetairoa McMillan", "CAR"), (16, "Jameson Williams", "DET"),
    (17, "Tee Higgins", "CIN"), (18, "Mike Evans", "SF"),
    (19, "Luther Burden", "CHI"), (20, "Ladd McConkey", "LAC"),
    (21, "DeVonta Smith", "PHI"), (22, "Terry McLaurin", "WAS"),
    (23, "Emeka Egbuka", "TB"), (24, "Rashee Rice", "KC"),
    (25, "Christian Watson", "GB"), (26, "Alec Pierce", "IND"),
    (27, "Rome Odunze", "CHI"), (28, "Parker Washington", "JAC"),
    (29, "Davante Adams", "LAR"), (30, "Jaylen Waddle", "DEN"),
    (31, "Carnell Tate", "TEN"), (32, "Brian Thomas", "JAC"),
    (33, "DK Metcalf", "PIT"), (34, "DJ Moore", "BUF"),
    (35, "Marvin Harrison", "ARI"), (36, "Jordyn Tyson", "NO"),
    (37, "Michael Wilson", "ARI"), (38, "Ricky Pearsall", "SF"),
    (39, "Chris Godwin", "TB"), (40, "Courtland Sutton", "DEN"),
    (41, "Romeo Doubs", "NE"), (42, "Makai Lemon", "PHI"),
    (43, "Jayden Reed", "GB"), (44, "Jakobi Meyers", "JAC"),
    (45, "Jayden Higgins", "HOU"), (46, "Xavier Worthy", "KC"),
    (47, "Quentin Johnston", "LAC"), (48, "Stefon Diggs", "WAS"),
    (49, "Jordan Addison", "MIN"), (50, "Jalen Coker", "CAR"),
    (51, "Michael Pittman", "PIT"), (52, "Matthew Golden", "GB"),
    (53, "Josh Downs", "IND"), (54, "Khalil Shakir", "BUF"),
    (55, "Wan'Dale Robinson", "TEN"), (56, "Omar Cooper", "NYJ"),
    (57, "KC Concepcion", "CLE"), (58, "Denzel Boston", "CLE"),
    (59, "Jalen Nailor", "LV"), (60, "Rashid Shaheed", "SEA"),
    (61, "Jauan Jennings", "MIN"), (62, "Brandon Aiyuk", "SF"),
    (63, "Deebo Samuel", "FA"), (64, "Jalen McMillan", "TB"),
    (65, "Jerry Jeudy", "CLE"), (66, "Tyreek Hill", "FA"),
    (67, "Kayshon Boutte", "NE"), (68, "Ryan Flournoy", "DAL"),
    (69, "Tre' Harris", "LAC"), (70, "De'Zhaun Stribling", "SF"),
    (71, "Tre Tucker", "LV"), (72, "Isaac TeSlaa", "DET"),
    (73, "Tory Horton", "SEA"), (74, "Ted Hurst", "TB"),
    (75, "Malik Washington", "MIA"), (76, "Zachariah Branch", "ATL"),
    (77, "Germie Bernard", "PIT"), (78, "Tank Dell", "HOU"),
    (79, "Antonio Williams", "WAS"), (80, "Travis Hunter", "JAC"),
    (81, "Pat Bryant", "DEN"), (82, "Darius Slayton", "NYG"),
    (83, "Skyler Bell", "BUF"), (84, "Keenan Allen", "FA"),
    (85, "DeMario Douglas", "NE"), (86, "Andrei Iosivas", "CIN"),
    (87, "Chris Bell", "MIA"), (88, "Devaughn Vele", "NO"),
    (89, "Ja'Kobi Lane", "BAL"), (90, "Elijah Sarratt", "BAL"),
    (91, "Malachi Fields", "NYG"), (92, "Jack Bech", "LV"),
    (93, "Dontayvion Wicks", "PHI"), (94, "Chimere Dike", "TEN"),
    (95, "Mack Hollins", "NE"), (96, "Chris Brazzell", "CAR"),
]

TES = [
    (1, "Trey McBride", "ARI"), (2, "Brock Bowers", "LV"),
    (3, "Colston Loveland", "CHI"), (4, "Tyler Warren", "IND"),
    (5, "Harold Fannin", "CLE"), (6, "Sam LaPorta", "DET"),
    (7, "Kyle Pitts", "ATL"), (8, "Tucker Kraft", "GB"),
    (9, "Travis Kelce", "KC"), (10, "Mark Andrews", "BAL"),
    (11, "Jake Ferguson", "DAL"), (12, "Dalton Kincaid", "BUF"),
    (13, "Brenton Strange", "JAC"), (14, "George Kittle", "SF"),
    (15, "Oronde Gadsden", "LAC"), (16, "Isaiah Likely", "NYG"),
    (17, "Hunter Henry", "NE"), (18, "Dallas Goedert", "PHI"),
    (19, "AJ Barner", "SEA"), (20, "Juwan Johnson", "NO"),
    (21, "Kenyon Sadiq", "NYJ"), (22, "Dalton Schultz", "HOU"),
    (23, "T.J. Hockenson", "MIN"), (24, "Pat Freiermuth", "PIT"),
    (25, "Cade Otton", "TB"), (26, "Chig Okonkwo", "WAS"),
    (27, "Gunnar Helm", "TEN"), (28, "Eli Stowers", "PHI"),
    (29, "Mike Gesicki", "CIN"), (30, "Darnell Washington", "PIT"),
    (31, "Darren Waller", "FA"), (32, "Colby Parkinson", "LAR"),
    (33, "Max Klare", "LAR"), (34, "Terrance Ferguson", "LAR"),
    (35, "David Njoku", "LAC"), (36, "Dawson Knox", "BUF"),
]

KICKERS = [
    (1, "Brandon Aubrey", "DAL"), (2, "Ka'imi Fairbairn", "HOU"),
    (3, "Jason Myers", "SEA"), (4, "Cameron Dicker", "LAC"),
    (5, "Cam Little", "JAC"), (6, "Will Reichard", "MIN"),
    (7, "Chase McLaughlin", "TB"), (8, "Jake Bates", "DET"),
    (9, "Eddy Pineiro", "SF"), (10, "Tyler Loop", "BAL"),
    (11, "Cairo Santos", "CHI"), (12, "Andres Borregales", "NE"),
    (13, "Harrison Mevis", "LAR"), (14, "Harrison Butker", "KC"),
    (15, "Chris Boswell", "PIT"), (16, "Tyler Bass", "BUF"),
    (17, "Charlie Smyth", "NO"), (18, "Wil Lutz", "DEN"),
    (19, "Evan McPherson", "CIN"), (20, "Blake Grupe", "IND"),
    (21, "Trey Smack", "GB"), (22, "Nick Folk", "ATL"),
    (23, "Jake Elliott", "PHI"), (24, "Joey Slye", "TEN"),
    (25, "Jake Moody", "WAS"), (26, "Jason Sanders", "NYG"),
    (27, "Ryan Fitzgerald", "CAR"), (28, "Chad Ryland", "ARI"),
    (29, "Matt Gay", "LV"), (30, "Zane Gonzalez", "MIA"),
    (31, "Andre Szmyt", "CLE"), (32, "Cade York", "NYJ"),
]

TEAMS_PER_LEAGUE = 10
ROUNDS = 18
DRAFT_ORDER = ["Vinayak", "Arjun", "Toby", "Vinny", "Jonathan", "Beatbug", "Kevin", "Dixon", "Kasper", "Justin"]


def connect_sheets():
    creds_json_str = os.getenv("GOOGLE_CREDS_JSON")
    if not creds_json_str:
        print("ERROR: GOOGLE_CREDS_JSON not found in .env"); sys.exit(1)
    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        print("ERROR: GOOGLE_SHEET_ID not found in .env"); sys.exit(1)
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds_dict = json.loads(creds_json_str)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds).open_by_key(sheet_id)


def update_player_board(ps):
    """Completely clear and rewrite the Player Board."""
    print("\n--- Updating Player Board ---")

    # The bot reads player names from these EXACT columns:
    # QB: col C (3), RB: col H (8), WR: col M (13), TE: col R (18), K: col W (23)
    #
    # Layout per position (6 columns per group, 5 used):
    #   Col-2: Rank  |  Col-1: Player  |  Col: (bot reads this, we put empty)
    #   Wait - the bot reads cols 3,8,13,18,23. If we put player names there
    #   and rank in col-1, the bot will read player names correctly.
    #
    # SIMPLE APPROACH: Put player names where the bot reads them.
    #   C=QB player, H=RB player, M=WR player, R=TE player, W=K player
    #   Rank goes one column left (B, G, L, Q, V)
    #   Team goes one column right (D, I, N, S, X)

    # First, NUCLEAR CLEAR: clear all of A-Z, rows 1-300
    print("  Clearing ALL existing data from Player Board...")
    ps.batch_clear(["A1:Z300"])

    # Position config: (label, data, player_col, rank_col, team_col)
    positions = [
        ("QB",  QBS,     3, 2, 4),   # C=player, B=rank, D=team
        ("RB",  RBS,      8, 7, 9),   # H=player, G=rank, I=team
        ("WR",  WRS,     13, 12, 14), # M=player, L=rank, N=team
        ("TE",  TES,     18, 17, 19), # R=player, Q=rank, S=team
        ("K",   KICKERS, 23, 22, 24), # W=player, V=rank, X=team
    ]

    HEADER_ROW = 3
    DATA_START = 4

    for label, players, pc, rc, tc in positions:
        print(f"  Writing {label}s ({len(players)} players)...")

        # Write headers
        ps.update_cell(HEADER_ROW, rc, "Rank")
        ps.update_cell(HEADER_ROW, pc, "Player")
        ps.update_cell(HEADER_ROW, tc, "Team")

        # Write data in batches
        cells = []
        for i, (rank, name, team) in enumerate(players):
            r = DATA_START + i
            cells.append({"range": f"{_col(rc)}{r}", "values": [[rank]]})
            cells.append({"range": f"{_col(pc)}{r}", "values": [[name]]})
            cells.append({"range": f"{_col(tc)}{r}", "values": [[team]]})

        for j in range(0, len(cells), 100):
            ps.batch_update(cells[j:j+100], value_input_option="USER_ENTERED")

    # Add position labels in row 1 via batch
    label_cells = [{"range": f"{_col(c)}1", "values": [[l]]} for l, c in
                   [("QB", 2), ("RB", 7), ("WR", 12), ("TE", 17), ("K", 22)]]
    ps.batch_update(label_cells, value_input_option="USER_ENTERED")

    print("  Player Board updated!")


def reset_draft_board(ds):
    """Reset the Draft Board to 10 teams, 18 rounds, clean slate."""
    print("\n--- Resetting Draft Board ---")

    # Nuclear clear
    print("  Clearing old draft data...")
    ds.batch_clear(["A3:Z500"])
    time.sleep(0.5)

    SC = 4  # Start at column D
    updates = []

    # Team headers row 3 (cols D-M) + "Round" in A3
    updates.append({"range": "A3", "values": [["Round"]]})
    for i, name in enumerate(DRAFT_ORDER):
        updates.append({"range": f"{_col(SC + i)}3", "values": [[name]]})

    # Pick numbers 1-10 in row 4
    for i in range(TEAMS_PER_LEAGUE):
        updates.append({"range": f"{_col(SC + i)}4", "values": [[str(i + 1)]]})

    # Round numbers in column A, rows 5+
    for rnd in range(ROUNDS):
        updates.append({"range": f"A{5 + rnd * 2}", "values": [[str(rnd + 1)]]})

    # Sidebar headers: Pick#, Drafted, Trades, Draft Order
    updates.append({"range": "Q3", "values": [["Pick #"]]})
    updates.append({"range": "Q4", "values": [[1]]})
    updates.append({"range": "R3", "values": [["Drafted"]]})
    updates.append({"range": "S3", "values": [["Trades"]]})
    updates.append({"range": "T3", "values": [["Draft Order"]]})

    # Snake draft order in column T
    rev = DRAFT_ORDER[::-1]
    full = []
    for rnd in range(ROUNDS):
        full.extend(DRAFT_ORDER if rnd % 2 == 0 else rev)
    for i, name in enumerate(full):
        updates.append({"range": f"T{4 + i}", "values": [[name]]})

    # Send all cell updates in chunks
    print(f"  Writing {len(updates)} cells in batches...")
    for j in range(0, len(updates), 50):
        chunk = updates[j:j+50]
        ds.batch_update(chunk, value_input_option="USER_ENTERED")
        time.sleep(0.3)  # avoid rate limit

    # ---- Apply formatting ----
    print("  Applying formatting...")
    time.sleep(1.0)

    ds.format(f"D5:M{4 + ROUNDS * 2}", {
        "backgroundColor": {"red": 0.85, "green": 0.85, "blue": 0.85}
    })
    time.sleep(0.5)

    ds.format(f"D3:M4", {
        "backgroundColor": {"red": 0.2, "green": 0.2, "blue": 0.4},
        "textFormat": {
            "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
            "bold": True,
            "fontSize": 10,
        },
        "horizontalAlignment": "CENTER",
    })

    print(f"  Draft Board reset! {len(full)} total picks ({ROUNDS} rounds x {TEAMS_PER_LEAGUE} teams)")


def _col(n):
    """Convert column number to letter (1=A, 2=B, ..., 26=Z)."""
    return chr(64 + n) if 1 <= n <= 26 else "?"


def main():
    print("=" * 50)
    print("2026 Fantasy Draft - Sheet Update (FIXED)")
    print("=" * 50)
    sheet = connect_sheets()
    print(f"Connected: '{sheet.title}'")

    ds = sheet.sheet1  # Draft Board
    ps = sheet.get_worksheet(1)  # Player Board
    print(f"Tabs: '{ds.title}', '{ps.title}'")

    update_player_board(ps)
    reset_draft_board(ds)

    print("\n" + "=" * 50)
    print("Done! Check your sheet.")
    print("=" * 50)


if __name__ == "__main__":
    main()
