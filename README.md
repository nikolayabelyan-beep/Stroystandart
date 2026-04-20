# StroyStandart Autonomous Office

Automation stack for office workflows in a construction company:
- Telegram control center
- Role-based agents (Director, PTO, Legal QA, Finance)
- Protocol-driven document flow
- Legal updates fetcher
- iOS control app + mobile API
- Excel accounting workbook as 1C alternative

## Quick start
1. Create env file:
   - `cp .env.example .env`
2. Fill keys in `.env`.
3. Run mobile API:
   - `python3 src/api/mobile_control_server.py --host 0.0.0.0 --port 8787`
4. Run Telegram bot:
   - `python3 -m src.bot.telegram_app`

## iPhone control
- iOS app source: `ios/StroyStandartOfficeApp/`
- API URL in app: `http://<YOUR_MAC_IP>:8787`

## Important
- Do not commit `.env` or any production secrets.
- Legal references must be verified via:
  - `obsidian_vault/01_Law/LEGAL_REFERENCE_INDEX.md`
  - `obsidian_vault/01_Law/Updates/LATEST_UPDATES.md`
