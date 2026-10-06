# Kvitto Payments

Тестовый сервис приёма оплат для онлайн-школы через систему «Квитто».

Сервис позволяет:

- получать список тарифов;
- создавать платежи;
- применять промокод;
- рассчитывать рассрочку;
- получать информацию о платежах;
- обрабатывать банковские вебхуки;
- защищать вебхуки HMAC-подписью;
- обеспечивать идемпотентность создания платежей.

Все денежные значения хранятся **только в копейках (`int`)**. Использование `float` полностью исключено.

> Проект выполнен с использованием ИИ-инструментов. Подробности и журнал работы находятся в файле `AI_LOG.md`.

---

# Технологии

- Python 3.11+
- FastAPI
- Pydantic v2
- SQLAlchemy Async
- SQLite (локально и в тестах)
- PostgreSQL (в Docker)
- Alembic
- pytest
- pytest-asyncio
- httpx
- Ruff
- Docker Compose
- GitHub Actions

---

# Структура проекта

```text
.
├── app
│   ├── api
│   │   └── routes
│   │       ├── payments.py      # Эндпоинты платежей
│   │       ├── tariffs.py       # Эндпоинты тарифов
│   │       └── webhooks.py      # Банковские вебхуки
│   │
│   ├── core
│   │   ├── config.py           # Настройки приложения
│   │   └── security.py         # HMAC-подпись вебхуков
│   │
│   ├── db
│   │   ├── base.py             # Declarative Base
│   │   ├── session.py          # AsyncSession и подключение к БД
│   │   └── seed.py             # Начальные данные
│   │
│   ├── models
│   │   ├── payment.py          # ORM-модель платежа
│   │   └── tariff.py           # ORM-модель тарифа
│   │
│   ├── schemas
│   │   ├── payment.py          # Pydantic-схемы платежей
│   │   ├── tariff.py           # Pydantic-схемы тарифов
│   │   └── webhook.py          # Схемы вебхуков
│   │
│   ├── services
│   │   └── payment_service.py  # Бизнес-логика
│   │
│   └── main.py                 # Точка входа FastAPI
│
├── alembic
│   ├── versions                # Миграции
│   └── env.py                  # Конфигурация Alembic
│
├── tests
│   ├── conftest.py             # Тестовая БД и фикстуры
│   ├── test_api.py             # Интеграционные тесты API
│   └── test_payment_service.py # Юнит-тесты бизнес-логики
│
├── .env.example
├── .gitignore
├── .dockerignore
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── alembic.ini
├── AI_LOG.md
└── README.md
```

---

# Получение проекта

Склонируйте репозиторий и перейдите в каталог проекта:

```bash
git clone https://github.com/IceM1le/kvitto-payments-api.git
cd kvitto-payments-api
```

---

# Локальный запуск без Docker

## 1. Создать виртуальное окружение

### PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Bash

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 2. Установить зависимости

```bash
pip install -e ".[dev]"
```

---

## 3. Создать `.env`

### PowerShell

```powershell
Copy-Item .env.example .env
```

### Bash

```bash
cp .env.example .env
```

---

## 4. Применить миграции

```bash
alembic upgrade head
```

---

## 5. Запустить приложение

```bash
uvicorn app.main:app --reload
```

---

## 6. Проверить работу

### PowerShell

```powershell
curl.exe http://127.0.0.1:8000/health
```

### Bash

```bash
curl http://127.0.0.1:8000/health
```

Ответ:

```json
{
  "status": "ok"
}
```

---

# Запуск через Docker

Запуск:

```bash
docker compose up --build
```

При старте контейнера `entrypoint.sh`:

1. ждёт готовности PostgreSQL;
2. выполняет `alembic upgrade head`;
3. запускает Uvicorn.

Проверка:

```bash
curl http://localhost:8000/tariffs
```

Остановка:

```bash
docker compose down
```

---

# Тесты

Проект содержит **26 тестов**.

Тесты работают на SQLite In-Memory и не требуют:

- PostgreSQL;
- Docker;
- Alembic.

Запуск:

```bash
pytest -v
```

---

# Линтер

Проверка:

```bash
ruff check .
```

Автоисправление:

```bash
ruff check . --fix
```

---

# Примеры API

## Получить тарифы

### PowerShell

```powershell
curl.exe http://127.0.0.1:8000/tariffs
```

### Bash

```bash
curl http://127.0.0.1:8000/tariffs
```

---

## Создать платёж (карта)

### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d "{\"tariff_id\":1,\"email\":\"user@example.com\",\"method\":\"card\"}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d '{"tariff_id":1,"email":"user@example.com","method":"card"}'
```

---

## Создать платёж с промокодом

Промокод:

```text
KVITTO10
```


### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d "{\"tariff_id\":2,\"email\":\"user@example.com\",\"method\":\"card\",\"promo_code\":\"kvitto10\"}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d '{"tariff_id":2,"email":"user@example.com","method":"card","promo_code":"kvitto10"}'
```

Для тарифа `1990000` копеек:

```json
{
  "amount": 1791000,
  "discount": 199000
}
```

---

## Создать платёж в рассрочку

### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d "{\"tariff_id\":2,\"email\":\"user@example.com\",\"method\":\"installment\",\"installment_months\":3}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -d '{"tariff_id":2,"email":"user@example.com","method":"installment","installment_months":3}'
```

Фрагмент ответа:

```json
{
  "amount": 1990000,
  "schedule": [
    663334,
    663333,
    663333
  ]
}
```

Проверка:

```text
663334 + 663333 + 663333 = 1990000
```

---

## Идемпотентность

Первый запрос:

### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" -d "{\"tariff_id\":1,\"email\":\"user@example.com\",\"method\":\"card\"}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" -d '{"tariff_id":1,"email":"user@example.com","method":"card"}'
```

Ответ:

```http
201 Created
```

Повторный запрос с тем же ключом:

### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" -d "{\"tariff_id\":1,\"email\":\"user@example.com\",\"method\":\"card\"}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/payments" -H "Content-Type: application/json" -H "Idempotency-Key: demo-key-1" -d '{"tariff_id":1,"email":"user@example.com","method":"card"}'
```

Ответ:

```http
200 OK
```

ID платежа будет тем же самым.

---

## Получить платёж по ID

### PowerShell

```powershell
curl.exe http://127.0.0.1:8000/payments/1
```

### Bash

```bash
curl http://127.0.0.1:8000/payments/1
```

---

## Фильтрация платежей

По email:

### PowerShell

```powershell
curl.exe "http://127.0.0.1:8000/payments?email=user@example.com"
```

### Bash

```bash
curl "http://127.0.0.1:8000/payments?email=user@example.com"
```

По статусу:

### PowerShell

```powershell
curl.exe "http://127.0.0.1:8000/payments?status=pending"
```

### Bash

```bash
curl "http://127.0.0.1:8000/payments?status=pending"
```

По email и статусу одновременно:

### PowerShell

```powershell
curl.exe "http://127.0.0.1:8000/payments?email=user@example.com&status=pending"
```

### Bash

```bash
curl "http://127.0.0.1:8000/payments?email=user@example.com&status=pending"
```

---

# Банковский вебхук (HMAC)

Вебхук требует заголовок:

```text
X-Signature
```

Подпись считается как:

```text
HMAC-SHA256(body, WEBHOOK_SECRET)
```

от **сырых байтов тела запроса**.

---

## Генерация подписи

Локальный секрет по умолчанию:

```text
local-development-secret
```

В Docker используется значение из переменной окружения:

```text
WEBHOOK_SECRET
```

### PowerShell

```powershell
python -c "import json,hmac,hashlib; body=json.dumps({'payment_id':1,'status':'succeeded'}, separators=(',', ':')).encode(); print(hmac.new(b'dev-secret-in-docker', body, hashlib.sha256).hexdigest())"
```

### Bash

```bash
python -c 'import hmac,hashlib; body=b"{\"payment_id\":1,\"status\":\"succeeded\"}"; print(hmac.new(b"dev-secret-in-docker", body, hashlib.sha256).hexdigest())'
```

### Важно

Тело запроса должно совпадать **байт-в-байт** с тем, от которого считалась подпись:

- тот же порядок ключей;
- те же кавычки;
- без дополнительных пробелов;
- без форматирования JSON.

Если подпись считалась от:

```json
{"payment_id":1,"status":"succeeded"}
```

то в `curl` нужно отправлять именно это тело без изменений.

---

## Отправка вебхука

Сначала создайте платёж через `POST /payments` и сохраните значение `id` из ответа.

Затем используйте этот `payment_id` в теле вебхука.

> Не предполагается, что платёж с `id=1` уже существует. Замените `1` в примерах ниже на реальный идентификатор созданного платежа.

### PowerShell

```powershell
curl.exe --% -X POST "http://127.0.0.1:8000/webhooks/bank" -H "Content-Type: application/json" -H "X-Signature: ВАША_ПОДПИСЬ" -d "{\"payment_id\":1,\"status\":\"succeeded\"}"
```

### Bash

```bash
curl -X POST "http://127.0.0.1:8000/webhooks/bank" -H "Content-Type: application/json" -H "X-Signature: ВАША_ПОДПИСЬ" -d '{"payment_id":1,"status":"succeeded"}'
```

Успешный ответ:

```json
{
  "result": "ok"
}
```

Запрещённый переход статуса:

```json
{
  "error": "invalid_transition"
}
```

с кодом:

```http
409 Conflict
```

---

# Переменные окружения

Файл:

```text
.env
```

Шаблон:

```text
.env.example
```

---

## DATABASE_URL

Локально:

```text
sqlite+aiosqlite:///./kvitto.db
```

Docker:

```text
postgresql+asyncpg://user:pass@db:5432/kvitto
```

---

## WEBHOOK_SECRET

Используется для проверки HMAC-подписей банковских вебхуков.

Пример:

```text
WEBHOOK_SECRET=local-development-secret
```

---

# Alembic

Применить миграции:

```bash
alembic upgrade head
```

Создать новую миграцию:

```bash
alembic revision --autogenerate -m "message"
```

Откатить последнюю миграцию:

```bash
alembic downgrade -1
```

Текущая версия:

```bash
alembic current
```

---

## Важно

Не рекомендуется запускать миграции при работающем Uvicorn-процессе, который уже использует ту же базу данных.

Сначала остановите приложение, затем выполняйте миграции.

---

# Частые проблемы

### 1. Ошибка `table tariffs already exists`

База данных уже содержит таблицы, которые Alembic пытается создать повторно. Проверьте состояние базы и историю миграций перед повторным запуском `alembic upgrade head`.

### 2. Миграции не применяются из-за работающего Uvicorn

Запущенное приложение может удерживать SQLite-файл открытым. Остановите Uvicorn и только после этого выполняйте миграции.

### 3. Docker не поднимается после изменений

Причиной может быть старый Docker volume с устаревшими данными PostgreSQL. Проверьте состояние контейнеров и томов перед повторным запуском.

### 4. Вебхук возвращает `401 Unauthorized`

Чаще всего HMAC-подпись рассчитана не от того тела запроса. Тело в `curl` должно совпадать с телом, использованным при расчёте подписи, байт-в-байт.

### 5. Вебхук возвращает `404 Not Found`

Передан несуществующий `payment_id`. Сначала создайте платёж через `POST /payments`, затем используйте его реальный идентификатор.

### 6. Промокод возвращает `422`

Допустимы только:

```text
KVITTO10
kvitto10
```

Любой другой промокод считается неизвестным.

---

# Работа с ИИ

Во время выполнения проекта использовались ИИ-инструменты для:

- генерации черновиков архитектуры;
- подготовки шаблонов кода;
- поиска вариантов реализации.

Каждое изменение проверялось вручную.

Все найденные ошибки, исправления и вклад ИИ подробно описаны в:

```text
AI_LOG.md
```

---