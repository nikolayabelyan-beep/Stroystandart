# iOS клиент: StroyStandart Office

## Что это
Нативный SwiftUI-клиент для iPhone, который управляет офисной автоматизацией через мобильный API:
- проверка доступности сервера,
- запуск обновления юридической базы,
- просмотр статуса последнего юридического отчета,
- получение ссылки на dashboard.

## Серверная часть
Запуск API-шлюза:
```bash
python3 src/api/mobile_control_server.py --host 0.0.0.0 --port 8787
```

Эндпоинты:
- `GET /health`
- `GET /dashboard-url`
- `GET /law/latest`
- `POST /law/update`

## Сборка iOS в Xcode
1. Откройте Xcode -> `File` -> `New` -> `Project` -> `App` (iOS, SwiftUI).
2. Название: `StroyStandartOffice`.
3. Замените созданные файлы на содержимое из:
   - `App/StroyStandartOfficeApp.swift`
   - `App/ContentView.swift`
   - `Services/APIClient.swift`
   - `Models/LawUpdateModels.swift`
4. В Signing & Capabilities укажите ваш Team.
5. В `APIClient.swift` задайте `baseURL`:
   - Симулятор: `http://127.0.0.1:8787`
   - Реальный iPhone в одной сети: `http://<IP_MAC>:8787`
   - Внешний доступ: `https://<ваш_tunnel_url>`
6. Запустите на устройстве: `Product -> Run`.

## Рекомендации по продакшену
- Добавить auth-токен между iOS и API.
- Вынести baseURL в Settings экрана.
- Добавить push-уведомления о критических сроках контрактов.
