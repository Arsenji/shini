import json
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_PATH = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.insert(0, str(BACKEND_PATH))

load_dotenv(BACKEND_PATH / ".env")
load_dotenv(Path(__file__).resolve().parent / ".env")

import logging

from app.database.session import SessionLocal  # noqa: E402
from app.models.order import OrderStatus  # noqa: E402
from app.services.order_service import OrderService  # noqa: E402

logger = logging.getLogger(__name__)


def get_manager_name(vk, user_id: int) -> str:
    users = vk.users.get(user_ids=user_id, fields="first_name,last_name")
    if not users:
        return "Менеджер"
    user = users[0]
    parts = [user.get("first_name", ""), user.get("last_name", "")]
    name = " ".join(part for part in parts if part).strip()
    return name or "Менеджер"


def handle_order_callback(vk, event_object: dict) -> str:
    order_id: int | None = None
    try:
        payload_raw = event_object.get("payload")
        if not payload_raw:
            return "Некорректное действие"

        if isinstance(payload_raw, str):
            payload = json.loads(payload_raw)
        else:
            payload = payload_raw

        order_id = int(payload["order_id"])
        action = payload["action"]
        user_id = int(event_object["user_id"])

        db = SessionLocal()
        try:
            service = OrderService(db)
            manager_name = get_manager_name(vk, user_id)

            if action == "take":
                order = service.update_status(
                    order_id=order_id,
                    status=OrderStatus.IN_PROGRESS,
                    manager_name=manager_name,
                    manager_vk_id=user_id,
                )
                logger.info("Order %s taken by %s", order.id, manager_name)
                return f"Заявка №{order.id} взята в работу"

            if action == "done":
                order = service.update_status(order_id=order_id, status=OrderStatus.DONE)
                logger.info("Order %s completed", order.id)
                return f"Заявка №{order.id} завершена"

            if action == "cancel":
                order = service.update_status(order_id=order_id, status=OrderStatus.CANCELED)
                logger.info("Order %s canceled", order.id)
                return f"Заявка №{order.id} отменена"

            return "Неизвестное действие"
        finally:
            db.close()
    except ValueError as error:
        logger.warning("Order callback error: %s", error)
        return str(error)
    except Exception:
        logger.exception("Failed to process order callback for order %s", order_id)
        return "Ошибка обработки заявки"


def answer_callback(vk, event_object: dict, text: str) -> None:
    vk.messages.sendMessageEventAnswer(
        event_id=event_object["event_id"],
        user_id=event_object["user_id"],
        peer_id=event_object["peer_id"],
        event_data=json.dumps({"type": "show_snackbar", "text": text}, ensure_ascii=False),
    )
