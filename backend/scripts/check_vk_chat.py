#!/usr/bin/env python3
"""Поиск peer_id беседы менеджеров для заявок с сайта.

Как советует поддержка VK:
1) Long Poll / Callback — событие message_new (см. режим --listen)
2) messages.getConversations + при необходимости getConversationsById

Примеры:
  python scripts/check_vk_chat.py
  python scripts/check_vk_chat.py --listen
  python scripts/check_vk_chat.py --send-test 42
  python scripts/check_vk_chat.py --probe-from 1 --probe-to 50
"""

from __future__ import annotations

import os
import sys
import time
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
CHAT_PEER_OFFSET = 2_000_000_000


def vk_call(method: str, **params) -> dict | list | int | str:
    payload = {
        **params,
        "access_token": VK_TOKEN,
        "v": VK_API_VERSION,
    }
    response = httpx.post(f"https://api.vk.com/method/{method}", data=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    if "error" in data:
        err = data["error"]
        raise RuntimeError(f"[{err.get('error_code')}] {err.get('error_msg')}")
    return data["response"]


def print_env_hint(chat_local_id: int, peer_id: int) -> None:
    print("\nЧто прописать для отправки В БЕСЕДУ (не в ЛС):")
    print("  # убери или очисти VK_PEER_ID — иначе заявки уйдут в личку")
    print("  VK_PEER_ID=")
    print(f"  VK_CHAT_ID={chat_local_id}")
    print("  # либо одной строкой полный peer_id беседы:")
    print(f"  # VK_PEER_ID={peer_id}")
    print("\nНа Render: удалите значение VK_PEER_ID (user_id менеджера) и задайте VK_CHAT_ID.")


def resolve_group_id() -> int:
    groups = vk_call("groups.getById")
    group = groups[0] if isinstance(groups, list) else groups["groups"][0]
    group_id = int(group.get("id"))
    print(f"Сообщество «{group.get('name')}» id={group_id}")
    if VK_GROUP_ID and str(group_id) != str(VK_GROUP_ID):
        print(f"Внимание: в .env VK_GROUP_ID={VK_GROUP_ID}, а токен от {group_id}")
    return group_id


def list_conversations() -> list[tuple[int, int, str]]:
    conv = vk_call("messages.getConversations", count=200, filter="all")
    items = conv.get("items", []) if isinstance(conv, dict) else []
    print(f"\nДиалогов у сообщества: {len(items)}")
    chats: list[tuple[int, int, str]] = []

    for item in items:
        conversation = item.get("conversation", {})
        peer = conversation.get("peer", {})
        peer_id = int(peer.get("id", 0))
        peer_type = peer.get("type", "?")
        if peer_id >= CHAT_PEER_OFFSET:
            chat_local_id = peer_id - CHAT_PEER_OFFSET
            title = conversation.get("chat_settings", {}).get("title", "без названия")
            chats.append((chat_local_id, peer_id, title))
            print(f"  • беседа «{title}» → VK_CHAT_ID={chat_local_id}  peer_id={peer_id}")
        elif peer_type == "user":
            print(f"  • ЛС с пользователем peer_id={peer_id}")
        else:
            print(f"  • {peer_type} peer_id={peer_id}")

    return chats


def probe_conversations_by_id(start: int, end: int) -> list[tuple[int, int, str]]:
    """Перебор peer_ids через messages.getConversationsById (совет поддержки VK)."""
    print(f"\nПеребор peer_id {CHAT_PEER_OFFSET + start}…{CHAT_PEER_OFFSET + end} через getConversationsById…")
    found: list[tuple[int, int, str]] = []
    for chat_local_id in range(start, end + 1):
        peer_id = CHAT_PEER_OFFSET + chat_local_id
        try:
            data = vk_call("messages.getConversationsById", peer_ids=peer_id)
        except RuntimeError as error:
            # 100 / permission — беседы нет или нет доступа
            if "900" in str(error) or "917" in str(error) or "100" in str(error):
                continue
            print(f"  peer_id={peer_id}: {error}")
            continue

        items = data.get("items", []) if isinstance(data, dict) else []
        if not items:
            continue
        conversation = items[0]
        title = conversation.get("chat_settings", {}).get("title", "без названия")
        found.append((chat_local_id, peer_id, title))
        print(f"  ✓ «{title}» → VK_CHAT_ID={chat_local_id}  peer_id={peer_id}")
        time.sleep(0.34)

    if not found:
        print("  Ничего не найдено в этом диапазоне.")
    return found


def listen_for_chat_peer(group_id: int, timeout_sec: int = 120) -> int | None:
    """Ловим peer_id беседы из message_new (Long Poll Bots API)."""
    print("\nLong Poll: напишите любое сообщение В БЕСЕДЕ, где есть сообщество.")
    print(f"Жду до {timeout_sec} сек… (Ctrl+C — выход)\n")

    server = vk_call("groups.getLongPollServer", group_id=group_id)
    if not isinstance(server, dict):
        raise RuntimeError("Некорректный ответ groups.getLongPollServer")

    key = server["key"]
    server_url = server["server"]
    ts = server["ts"]
    deadline = time.time() + timeout_sec

    with httpx.Client(timeout=35) as client:
        while time.time() < deadline:
            response = client.get(
                server_url,
                params={"act": "a_check", "key": key, "ts": ts, "wait": 25},
            )
            response.raise_for_status()
            payload = response.json()

            if payload.get("failed"):
                # ключ/ts устарели — перезапрашиваем сервер
                server = vk_call("groups.getLongPollServer", group_id=group_id)
                assert isinstance(server, dict)
                key = server["key"]
                server_url = server["server"]
                ts = server["ts"]
                continue

            ts = payload.get("ts", ts)
            for update in payload.get("updates", []):
                if not isinstance(update, dict):
                    continue
                if update.get("type") != "message_new":
                    continue

                message = update.get("object", {}).get("message") or update.get("object", {})
                peer_id = int(message.get("peer_id", 0))
                from_id = message.get("from_id")
                text = (message.get("text") or "")[:80]
                print(f"message_new: peer_id={peer_id} from_id={from_id} text={text!r}")

                if peer_id >= CHAT_PEER_OFFSET:
                    chat_local_id = peer_id - CHAT_PEER_OFFSET
                    print(f"\n✓ Это беседа. VK_CHAT_ID={chat_local_id}  peer_id={peer_id}")
                    print_env_hint(chat_local_id, peer_id)
                    return peer_id

                print("  (это личка, не беседа — напишите именно в групповой чат)")

    print("Время вышло: событие из беседы не пришло.")
    return None


def send_test(chat_local_id: int) -> None:
    peer_id = CHAT_PEER_OFFSET + chat_local_id
    print(f"\nТест messages.send → VK_CHAT_ID={chat_local_id} (peer_id={peer_id})…")
    msg_id = vk_call(
        "messages.send",
        peer_id=peer_id,
        random_id=int(time.time() * 1000) % 2_000_000_000,
        message="✅ Тест: заявки КОЛЁСА ДЁШЕВО будут приходить в эту беседу",
    )
    print(f"OK, message_id={msg_id}")


def parse_args(argv: list[str]) -> dict:
    options: dict = {
        "listen": False,
        "send_test": None,
        "probe_from": None,
        "probe_to": None,
        "timeout": 120,
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--listen":
            options["listen"] = True
        elif arg == "--send-test":
            options["send_test"] = int(argv[i + 1]) if i + 1 < len(argv) and argv[i + 1].lstrip("-").isdigit() else 0
            if i + 1 < len(argv) and argv[i + 1].lstrip("-").isdigit():
                i += 1
        elif arg == "--probe-from":
            options["probe_from"] = int(argv[i + 1])
            i += 1
        elif arg == "--probe-to":
            options["probe_to"] = int(argv[i + 1])
            i += 1
        elif arg == "--timeout":
            options["timeout"] = int(argv[i + 1])
            i += 1
        elif arg.lstrip("-").isdigit() and options["send_test"] == 0:
            options["send_test"] = int(arg)
        i += 1

    # совместимость: --send-test без числа → 0 (возьмём первую найденную)
    if "--send-test" in argv and options["send_test"] is None:
        options["send_test"] = 0
    return options


def main() -> int:
    if not VK_TOKEN:
        print("Нет VK_TOKEN. Положите его в backend/.env или vk-tire-bot/.env")
        return 1

    options = parse_args(sys.argv[1:])

    print("1) Проверяю токен…")
    try:
        group_id = resolve_group_id()
    except Exception as error:
        print(f"Ошибка: {error}")
        print("Нужен токен сообщества (не пользовательский).")
        return 1

    current_peer = os.getenv("VK_PEER_ID", "").strip()
    current_chat = os.getenv("VK_CHAT_ID", "").strip()
    print("\nТекущие настройки из .env:")
    print(f"  VK_PEER_ID={current_peer or '(пусто)'}")
    print(f"  VK_CHAT_ID={current_chat or '(пусто)'}")
    if current_peer and int(current_peer) < CHAT_PEER_OFFSET:
        print("  ⚠ VK_PEER_ID указывает на ЛС пользователя — заявки идут в личку, не в беседу.")
        print("    Для беседы очистите VK_PEER_ID и задайте VK_CHAT_ID.")

    print("\n2) Список диалогов (messages.getConversations)…")
    try:
        chats = list_conversations()
    except Exception as error:
        print(f"Ошибка: {error}")
        print("Включите сообщения сообщества и право messages у ключа.")
        return 1

    if options["probe_from"] is not None:
        probe_to = options["probe_to"] if options["probe_to"] is not None else options["probe_from"] + 30
        probed = probe_conversations_by_id(options["probe_from"], probe_to)
        for item in probed:
            if item not in chats:
                chats.append(item)

    if chats:
        print("\nБеседы, куда можно слать заявки:")
        for chat_local_id, peer_id, title in chats:
            print(f"  • «{title}» → VK_CHAT_ID={chat_local_id}")
        print_env_hint(chats[0][0], chats[0][1])
    else:
        print("\nБесед в getConversations нет.")
        print("Добавьте сообщество в беседу (приглашение по ссылке),")
        print("затем напишите в чате любое сообщение @сообществу / боту.")
        print("Или запустите: python scripts/check_vk_chat.py --listen")

    if options["listen"]:
        try:
            listen_for_chat_peer(group_id, timeout_sec=options["timeout"])
        except KeyboardInterrupt:
            print("\nОстановлено.")
            return 0
        except Exception as error:
            print(f"Long Poll ошибка: {error}")
            return 1

    if options["send_test"] is not None:
        if options["send_test"] > 0:
            chat_id = options["send_test"]
        elif chats:
            chat_id = chats[0][0]
        else:
            print("Нечего тестировать: укажите --send-test <VK_CHAT_ID>")
            return 2
        try:
            send_test(chat_id)
        except Exception as error:
            print(f"Ошибка отправки: {error}")
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
