# Fantasy Draft Bot - 2026 Season

## Quick Reference
- **Fly.io dashboard:** https://fly.io/apps/fantasy-draft-bot-a0f0iw
- **Google Sheet:** https://docs.google.com/spreadsheets/d/1gG_KidU820YHv8aTObjeEMU6iBx7qdFZXs-IuK-iilI/edit
- **Service account:** draft-bot-runner@fantasy-draft-bot-2025.iam.gserviceaccount.com
- **GitHub:** https://github.com/MrBeatbug/fantasy-draft-bot

## Commands
- **Run locally:** `cd ~/fantasy-draft-bot && python3 main.py` (pause Fly first: `flyctl scale count 0`)
- **Deploy:** `flyctl deploy` (make sure to push to GitHub first)
- **Logs:** `flyctl logs`
- **Stop bot:** `flyctl scale count 0`
- **Start bot:** `flyctl scale count 1`
- **Sheet update:** `python3 update_sheets.py`

## Config
- **Teams (10):** Vinayak, Arjun, Toby, Vinny, Jonathan, Beatbug, Kevin, Dixon, Kasper, Justin
- **Rounds:** 18
- **Positions:** QB (36), RB (72), WR (96), TE (36), K (32), DEF (32)
- **Draft channel ID:** 1534410621607739454
- **Server ID:** 769749848911249448

## Key Files
- `main.py` — Discord bot
- `update_sheets.py` — Sheet reset/update script
- `fly.toml` — Fly.io deploy config
- `Procfile` — `web: python main.py`
- `.env` — Local credentials (not in git)
