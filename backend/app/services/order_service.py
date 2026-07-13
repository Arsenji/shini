import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models.order import Order, OrderStatus

logger = logging.getLogger(__name__)

MSK = ZoneInfo("Europe/Moscow")


def format_phone_display(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 11 and digits.startswith("7"):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


def format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return dt.astimezone(MSK).strftime("%d.%m.%Y %H:%M")


def status_emoji(status: OrderStatus) -> str:
    mapping = {
        OrderStatus.NEW: "🟡 Новая",
        OrderStatus.IN_PROGRESS: "🟢 В работе",
        OrderStatus.DONE: "✅ Завершена",
        OrderStatus.CANCELED: "❌ Отказ",
    }
    return mapping[status]


def build_order_message(order: Order) -> str:
    lines = [
        "🚗 Новая заявка",
        "",
        f"Заявка №{order.id}",
        "",
        "Размер:",
        "",
        order.size_label,
        "",
        "Телефон:",
        "",
        format_phone_display(order.phone),
        "",
        "Время:",
        "",
        format_datetime(order.created_at),
        "",
        "Статус:",
        "",
        status_emoji(order.status),
    ]

    if order.status == OrderStatus.IN_PROGRESS and order.manager_name:
        lines.extend(["", "Менеджер:", "", order.manager_name])

    return "\n".join(lines)


def build_order_keyboard(order: Order) -> str:
    buttons: list[dict] = []
    payload_prefix = {"order_id": order.id}

    if order.status == OrderStatus.NEW:
        buttons.append(
            {
                "action": {
                    "type": "callback",
                    "label": "🟢 Взять в работу",
                    "payload": json.dumps({**payload_prefix, "action": "take"}, ensure_ascii=False),
                },
                "color": "positive",
            }
        )
    elif order.status == OrderStatus.IN_PROGRESS:
        buttons.extend(
            [
                {
                    "action": {
                        "type": "callback",
                        "label": "✅ Завершено",
                        "payload": json.dumps({**payload_prefix, "action": "done"}, ensure_ascii=False),
                    },
                    "color": "positive",
                },
                {
                    "action": {
                        "type": "callback",
                        "label": "❌ Отказ",
                        "payload": json.dumps({**payload_prefix, "action": "cancel"}, ensure_ascii=False),
                    },
                    "color": "negative",
                },
            ]
        )

    keyboard = {"inline": True, "buttons": [buttons] if buttons else []}
    return json.dumps(keyboard, ensure_ascii=False)


class VKClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.base_url = "https://api.vk.com/method"

    def _post(self, method: str, params: dict) -> dict:
        payload = {
            **params,
            "access_token": self.settings.vk_token,
            "v": self.settings.vk_api_version,
        }
        with httpx.Client(timeout=20.0) as client:
            response = client.post(f"{self.base_url}/{method}", data=payload)
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            error = data["error"]
            logger.error("VK API error [%s]: %s", error.get("error_code"), error.get("error_msg"))
            raise RuntimeError(f"VK API error: {error.get('error_msg')}")

        return data["response"]

    def send_order_message(self, order: Order) -> tuple[int, int]:
        peer_id = self.settings.vk_peer_id
        message = build_order_message(order)
        keyboard = build_order_keyboard(order)

        try:
            response = self._post(
                "messages.send",
                {
                    "peer_id": peer_id,
                    "random_id": order.id,
                    "message": message,
                    "keyboard": keyboard,
                },
            )
        except RuntimeError as error:
            logger.warning("VK send with keyboard failed for order %s: %s", order.id, error)
            response = self._post(
                "messages.send",
                {
                    "peer_id": peer_id,
                    "random_id": order.id + 1_000_000,
                    "message": message,
                },
            )

        return peer_id, int(response)

    def edit_order_message(self, order: Order) -> None:
        if not order.vk_message_id or not order.vk_peer_id:
            logger.warning("Order %s has no VK message metadata", order.id)
            return

        self._post(
            "messages.edit",
            {
                "peer_id": order.vk_peer_id,
                "message_id": order.vk_message_id,
                "message": build_order_message(order),
                "keyboard": build_order_keyboard(order),
            },
        )


class OrderService:
    def __init__(self, db: Session, vk_client: VKClient | None = None) -> None:
        self.db = db
        self.vk = vk_client or VKClient()

    def create_order(self, width: int, profile: int, radius: int, phone: str) -> Order:
        order = Order(
            width=width,
            profile=profile,
            radius=radius,
            phone=phone,
            status=OrderStatus.NEW,
        )
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        logger.info("Order created: id=%s size=%s phone=%s", order.id, order.size_label, order.phone)

        try:
            peer_id, message_id = self.vk.send_order_message(order)
            order.vk_peer_id = peer_id
            order.vk_message_id = message_id
            self.db.commit()
            self.db.refresh(order)
            logger.info("VK message sent for order %s (message_id=%s)", order.id, message_id)
        except Exception as error:
            logger.exception("Failed to send VK message for order %s", order.id)
            raise RuntimeError(f"VK send failed for order {order.id}") from error

        return order

    def update_status(
        self,
        order_id: int,
        status: OrderStatus,
        manager_name: str | None = None,
        manager_vk_id: int | None = None,
    ) -> Order:
        order = self.db.get(Order, order_id)
        if order is None:
            raise ValueError(f"Заявка №{order_id} не найдена")

        if status == OrderStatus.IN_PROGRESS and order.status != OrderStatus.NEW:
            raise ValueError("Заявка уже взята в работу")

        if status in {OrderStatus.DONE, OrderStatus.CANCELED} and order.status != OrderStatus.IN_PROGRESS:
            raise ValueError("Заявку можно завершить только из статуса «В работе»")

        order.status = status
        if manager_name is not None:
            order.manager_name = manager_name
        if manager_vk_id is not None:
            order.manager_vk_id = manager_vk_id

        self.db.commit()
        self.db.refresh(order)
        logger.info(
            "Order %s status updated to %s (manager=%s)",
            order.id,
            order.status.value,
            order.manager_name,
        )

        try:
            self.vk.edit_order_message(order)
        except Exception:
            # Статус уже сохранён — не откатываем и не роняем callback у менеджера
            logger.exception(
                "Failed to edit VK message for order %s (status already saved as %s)",
                order.id,
                order.status.value,
            )

        return order
