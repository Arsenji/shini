# Backend: система заявок КОЛЁСА ДЁШЕВО

FastAPI-сервис для приёма заявок с сайта и отправки их в беседу менеджеров ВКонтакте.

## Стек

- Python 3.12
- FastAPI
- SQLAlchemy + Alembic
- PostgreSQL
- httpx (VK API)

## Быстрый старт (Docker)

```bash
cd backend
cp .env.example .env
# Заполните VK_TOKEN и VK_CHAT_ID в .env

docker compose up --build
```

API будет доступен на `http://localhost:8000`.

Проверка:

```bash
curl http://localhost:8000/health
```

## Локальный запуск без Docker

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Укажите DATABASE_URL, VK_TOKEN, VK_CHAT_ID

# PostgreSQL должен быть запущен
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `DATABASE_URL` | PostgreSQL, например `postgresql+psycopg://shini:shini@localhost:5432/shini` |
| `VK_TOKEN` | Токен сообщества VK |
| `VK_API_VERSION` | Версия API (по умолчанию `5.199`) |
| `VK_CHAT_ID` | ID беседы менеджеров (без `2000000000`) |
| `HOST` | Хост сервера (по умолчанию `0.0.0.0`) |
| `PORT` | Порт (по умолчанию `8000`) |
| `CORS_ORIGINS` | Разрешённые origin через запятую |

## API

### `POST /api/orders`

Тело запроса:

```json
{
  "width": 205,
  "profile": 55,
  "radius": 16,
  "phone": "+79991234567"
}
```

Ответ:

```json
{
  "success": true,
  "order_id": 15
}
```

Валидация:

- ширина: 100–395
- профиль: 20–95
- диаметр: 10–30
- телефон: российский номер

## Миграции

```bash
alembic upgrade head
alembic revision --autogenerate -m "описание"
```

## Подключение VK

1. Создайте беседу менеджеров и добавьте туда сообщество.
2. Включите **Чат-бот** в настройках сообщества.
3. Получите токен: Управление → Работа с API → Ключи доступа.
4. Узнайте `VK_CHAT_ID` беседы (число без префикса `2000000000`).
5. Запустите `vk-tire-bot` для обработки кнопок в беседе.

## VK-бот (кнопки в беседе)

Бот использует ту же PostgreSQL (`DATABASE_URL`) и обрабатывает callback-кнопки:

- 🟢 Взять в работу → `IN_PROGRESS`
- ✅ Завершено → `DONE`
- ❌ Отказ → `CANCELED`

```bash
cd vk-tire-bot
pip install -r requirements.txt
cp .env.example .env
python3 main.py
```

## Интеграция с React

Локально Vite проксирует `/api` на `http://localhost:8000`.

Для production на Vercel задайте:

```
VITE_API_URL=https://your-backend-domain.com
```

Форма в Hero отправляет `POST /api/orders` при нажатии «Получить расчёт».
