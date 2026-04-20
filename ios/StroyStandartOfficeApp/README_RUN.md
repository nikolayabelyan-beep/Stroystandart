# Run iOS App (stable)

1. Start automation services on Mac:
```bash
cd /Users/nikolajtamrazov/Documents/BACKUP_GOLD
./scripts/start_services.sh
```

2. Optional: install launchd for persistent API on reboot:
```bash
/Users/nikolajtamrazov/Documents/BACKUP_GOLD/scripts/install_mobile_api_launchd.sh
```

3. Verify API:
```bash
curl http://127.0.0.1:8787/health
curl http://127.0.0.1:8787/services/status
```

4. Open and run Xcode project:
```bash
open /Users/nikolajtamrazov/Documents/BACKUP_GOLD/ios/StroyStandartOfficeApp/StroyStandartOffice.xcodeproj
```

Notes:
- In app, use button `Автоисправление (1 кнопка)` to auto-find Mac API in LAN and ensure services are running.
- iPhone and Mac must be in the same Wi-Fi network.
- Manual URL field is still available as fallback.
