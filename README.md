# Sales Chat Bot

Чат-бот отдела продаж на Python/FastAPI и Node.js с поддержкой GigaChat, ProxyAPI и Telegram. Согласованные по интервью сценарий и критерии приёмки описаны в [SPECIFICATION.md](SPECIFICATION.md).

## Возможности

- профессиональное меню: товары, статус заказа, поддержка;
- демо-каталог с ценами и сроками;
- реалистичная база заказов и поиск по номеру;
- FAQ по доставке, срокам, оплате и возвратам;
- передача менеджеру без генерации неподтверждённых данных;
- сохранение контакта только после явного согласия;
- демо-CRM с лидами и аналитикой;
- GigaChat OAuth, ProxyAPI и автономный mock-режим;
- универсальный REST webhook и Telegram webhook.

## Быстрый запуск

```powershell
Copy-Item .env.example .env
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m uvicorn app.main:app --reload
```

Во втором терминале:

```powershell
Set-Location node-gateway
npm install
npm start
```

Swagger: `http://localhost:8000/docs`. По умолчанию используется `LLM_PROVIDER=mock`, поэтому ключи внешних сервисов для демонстрации не нужны.

## Проверка диалога

```powershell
$headers = @{ 'x-api-key' = 'change-me' }
$body = @{ session_id='demo-1'; message='/start'; channel='web' } | ConvertTo-Json
Invoke-RestMethod http://localhost:8000/api/v1/chat -Method Post -Headers $headers -ContentType application/json -Body $body
```

Демо-заказы: `ORD-1001`, `ORD-1002`, `ORD-1003`.

## REST API демо-системы

- `POST /api/v1/chat` — сообщение боту;
- `GET /api/v1/demo/products` — каталог;
- `GET /api/v1/demo/orders/{order_id}` — статус заказа;
- `GET /api/v1/demo/leads` — лиды;
- `GET /api/v1/metrics` — число диалогов, лидов, конверсия и темы.

## Telegram

Укажите `TELEGRAM_BOT_TOKEN` и `TELEGRAM_WEBHOOK_SECRET`, затем зарегистрируйте HTTPS-адрес `/webhook/telegram` как webhook бота. Без токена endpoint возвращает mock-ответ и подходит для приёмочной демонстрации.

## Тесты

```powershell
.venv\Scripts\python -m pytest -q
node --check node-gateway/src/server.js
```

Для production in-memory хранилища следует заменить на PostgreSQL/Redis, настроить HTTPS, ротацию секретов, журналирование без персональных данных и реальную CRM.
