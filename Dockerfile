FROM node:22-alpine AS frontend

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY index.html vite.config.ts tsconfig.json tsconfig.node.json ./
COPY public ./public
COPY src ./src

RUN npm run build

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY backend/requirements.txt .
COPY vk-tire-bot/requirements.txt ./vk-bot-requirements.txt
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r vk-bot-requirements.txt

COPY backend/ .
COPY vk-tire-bot ./vk-tire-bot
COPY --from=frontend /app/dist ./static

RUN chmod +x /app/start.sh

EXPOSE 8000

CMD ["/app/start.sh"]
