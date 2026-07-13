#!/usr/bin/env python3
"""Проверка токена VK и поиск ID беседы менеджеров."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BOT_ENV = ROOT.parent / "vk-tire-bot" / ".env"
BACKEND_ENV = ROOT / ".env"

load_dotenv(BOT_ENV)
load_dotenv(BACKEND_ENV, override=True)
if not os.getenv("VK_TOKEN", "").strip() and BOT_ENV.exists():
    load_dotenv(BOT_ENV, override=True)

VK_TOKEN = os.getenv("VK_TOKEN", "").strip()
VK_API_VERSION = os.getenv("VK_API_VERSION", "5.199")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "").strip()


def vk_call(method: str, **params) -> dict:
    payload = {
        **params,
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
    }
    response = httpx.post(f"https://api.vk.com/method/{method}", data=payload, timeout=20)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"[{err.get('error_code')}] {err.get('error_msg')}")
    return data["response"]


def main() -> int:
    if not VK_TOKEN:
        print("Нет VK_TOKEN. Положите его в backend/.env или vk-tire-bot/.env")
        return 1

    print("1) Проверяю токен...")
    try:
        groups = vk_call("groups.getById")
        group = groups[0] if isinstance(groups, list) else groups["groups"][0]
        print(f"   OK: сообщество «{group.get('name')}» id={group.get('id')}")
        if VK_GROUP_ID and str(group.get("id")) != str(VK_GROUP_ID):
            print(f"   Внимание: в .env VK_GROUP_ID={VK_GROUP_ID}, а токен от {group.get('id')}")
    except Exception as error:
        print(f"   Ошибка: {error}")
        print("   Проверьте, что токен — от сообщества (не пользовательский).")
        return 1

    print("\n2) Проверяю доступ к сообщениям...")
    try:
        conv = vk_call("messages.getConversations", count=20, filter="all")
        items = conv.get("items", [])
        print(f"   Найдено диалогов: {len(items)}")
    except Exception as error:
        print(f"   Ошибка: {error}")
        print("   Включите сообщения сообщества и права токена messages.")
        return 1

    chats = []
    for item in items:
        peer = item["conversation"]["peer"]
        peer_id = peer["id"]
        if peer_id < 2_000_000_000:
            continue
        chat_local_id = peer_id - 2_000_000_000
        title = item["conversation"].get("chat_settings", {}).get("title", "без названия")
        chats.append((chat_local_id, peer_id, title))

    send_test = len(sys.argv) > 1 and sys.argv[1] == "--send-test"
    send_test_chat_id = int(sys.argv[2]) if send_test and len(sys.argv) > 2 else None

    print("\n3) Беседы, где есть сообщество:")
    if not chats:
        print("   В списке диалогов бесед не видно.")
        if send_test_chat_id is not None:
            print(f"   Пробую отправить тест в VK_CHAT_ID={send_test_chat_id}...")
        else:
            print("   Добавьте сообщество в чат менеджеров или запустите:")
            print("   python scripts/check_vk_chat.py --send-test 197")
            return 2
    else:
        for chat_local_id, peer_id, title in chats:
            print(f"   • «{title}»")
            print(f"     VK_CHAT_ID={chat_local_id}")
            print(f"     peer_id={peer_id}")

        print("\n4) Что прописать в backend/.env:")
        print("   VK_TOKEN=...ваш токен...")
        print(f"   VK_CHAT_ID={chats[0][0]}")
        print(f"   VK_API_VERSION={VK_API_VERSION}")

    if send_test:
        chat_id = send_test_chat_id if send_test_chat_id is not None else chats[0][0]
        peer_id = 2_000_000_000 + chat_id
        print(f"\n5) Отправляю тестовое сообщение в беседу {chat_id} (peer_id={peer_id})...")
        try:
            msg_id = vk_call(
                "messages.send",
                peer_id=peer_id,
                random_id=0,
                message="✅ Тест: бот КОЛЁСА ДЁШЕВО видит эту беседу",
            )
            print(f"   OK, message_id={msg_id}")
        except Exception as error:
            print(f"   Ошибка отправки: {error}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
