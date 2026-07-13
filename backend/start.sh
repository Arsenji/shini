#!/bin/sh
set -eu

cd /app
alembic upgrade head

# Long Poll бот нужен для кнопок «Взять в работу» / «Завершено» / «Отказ»
(
  while true; do
    echo "[start] Запускаю VK Long Poll бот..."
    (cd /app/vk-tire-bot && python main.py) || true
    echo "[start] VK бот остановился, перезапуск через 5с..."
    sleep 5
  done
) &

exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
