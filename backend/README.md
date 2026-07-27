# Backend: система заявок КОЛЁСА ДЁШЕВО

FastAPI-сервис для приёма заявок с сайта и отправки их менеджеру в VK.

## Стек

- Python 3.12
- FastAPI
- httpx (VK API)

## Быстрый старт (Docker)

```bash
cd backend
cp .env.example .env
# Заполните VK_TOKEN и VK_PEER_ID в .env

docker compose up --build
```

API будет доступен на `http://localhost:8000`.

Проверка:

```bash
curl http://localhost:8000/health
```

## Локальный запуск

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Укажите VK_TOKEN, VK_PEER_ID

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Переменные окружения

| Переменная | Описание |
|------------|----------|
| `VK_TOKEN` | Токен сообщества VK |
| `VK_API_VERSION` | Версия API (по умолчанию `5.199`) |
| `VK_PEER_ID` | ID получателя(ей) в ЛС через запятую; приоритет над `VK_CHAT_ID` |
| `VK_CHAT_ID` | ID беседы (только если чат есть в сообщениях сообщества) |
| `HOST` | Хост сервера (по умолчанию `0.0.0.0`) |
| `PORT` | Порт (по умолчанию `8000`) |
| `CORS_ORIGINS` | Разрешённые origin через запятую |

## API

### `POST /api/orders`

Тело запроса:

```json
{
  "name": "Иван",
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
  "order_id": 1720912345
}
```

Валидация:

- имя: 2–40 символов, буквы
- ширина: 100–395
- профиль: 20–95
- диаметр: 10–30
- телефон: российский номер

## Подключение VK

1. Токен сообщества: Управление → Работа с API → Ключи доступа (права `messages`).
2. Куда слать заявки:

### Личные сообщения менеджерам (рекомендуется)

Работает стабильно. Можно несколько получателей через запятую:

```env
VK_PEER_ID=146507806,225909038
```

ID: профиль → `vk.com/idXXXXXXXX`. Пользователь должен разрешить сообщения от сообщества
(хотя бы раз написать сообществу в ЛС).

### Беседа сообщества

Работает только если чат виден в **Управление сообществом → Сообщения**.
Если чата там нет — API отвечает `927`; используйте ЛС выше.

```bash
cd backend && source .venv/bin/activate
python scripts/check_vk_chat.py
python scripts/check_vk_chat.py --listen
```

## Интеграция с React

Локально Vite проксирует `/api` на `http://localhost:8000`.

На production фронт и API на одном домене (Render Docker).

Формы в Hero и RequestForm отправляют `POST /api/orders`.
