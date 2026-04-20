# Run iOS App (stable)

1. Install + start persistent API service:
```bash
/Users/nikolajtamrazov/Documents/BACKUP_GOLD/scripts/install_mobile_api_launchd.sh
```

2. Verify API:
```bash
curl http://192.168.0.107:8787/health
```

3. Open and run Xcode project:
```bash
open /Users/nikolajtamrazov/Documents/BACKUP_GOLD/ios/StroyStandartOfficeApp/StroyStandartOffice.xcodeproj
```

Notes:
- iOS app uses `http://192.168.0.107:8787` by default.
- If your Mac IP changes, update URL in app field `API URL`.
