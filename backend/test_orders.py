"""Integration tests for backend order flow (SQLite + mocked VK)."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

# Ensure backend package is importable
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["VK_TOKEN"] = "test-token"
os.environ["VK_CHAT_ID"] = "100"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx

from app.config import get_settings
from app.database.session import get_db
from app.main import app
from app.models.order import Base, Order, OrderStatus
from app.schemas.order import OrderCreate, normalize_phone
from app.services.order_service import (
    OrderService,
    build_order_keyboard,
    build_order_message,
    format_phone_display,
)

get_settings.cache_clear()

engine = create_engine(
    "sqlite+pysqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

passed = 0
failed = 0


def check(name: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"PASS  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}" + (f" — {detail}" if detail else ""))


# --- Schema validation ---
check("phone +7 ok", normalize_phone("+79991234567") == "+79991234567")
check("phone 8... ok", normalize_phone("89991234567") == "+79991234567")
check("phone formatted ok", normalize_phone("+7 (999) 123-45-67") == "+79991234567")

try:
    normalize_phone("12345")
    check("phone invalid raises", False)
except ValueError:
    check("phone invalid raises", True)

try:
    OrderCreate(name="Иван", width=50, profile=55, radius=16, phone="+79991234567")
    check("width bounds", False)
except ValidationError:
    check("width bounds", True)

try:
    OrderCreate(name="Иван", width=205, profile=10, radius=16, phone="+79991234567")
    check("profile bounds", False)
except ValidationError:
    check("profile bounds", True)

try:
    OrderCreate(name="Иван", width=205, profile=55, radius=5, phone="+79991234567")
    check("radius bounds", False)
except ValidationError:
    check("radius bounds", True)

ok = OrderCreate(name="Иван", width=205, profile=55, radius=16, phone="8 (999) 123-45-67")
check("valid OrderCreate", ok.phone == "+79991234567")

# --- Message / keyboard ---
order = Order(
    id=15,
    customer_name="Иван",
    width=205,
    profile=55,
    radius=16,
    phone="+79991234567",
    status=OrderStatus.NEW,
    created_at=datetime(2026, 7, 13, 17, 45, tzinfo=timezone.utc),
    updated_at=datetime(2026, 7, 13, 17, 45, tzinfo=timezone.utc),
)
msg = build_order_message(order)
check("message has title", "🚗 Новая заявка" in msg)
check("message has order id", "Заявка №15" in msg)
check("message has customer name", "Иван" in msg)
check("message has size", "205/55 R16" in msg)
check("message has phone", "+7 (999) 123-45-67" in msg)
check("message has status new", "🟡 Новая" in msg)
check("phone display", format_phone_display("+79991234567") == "+7 (999) 123-45-67")

kb = json.loads(build_order_keyboard(order))
check("keyboard inline", kb.get("inline") is True)
check("keyboard take button", kb["buttons"][0][0]["action"]["label"] == "🟢 Взять в работу")
payload = json.loads(kb["buttons"][0][0]["action"]["payload"])
check("keyboard payload take", payload == {"order_id": 15, "action": "take"})

order.status = OrderStatus.IN_PROGRESS
order.manager_name = "Иван"
msg2 = build_order_message(order)
check("message in progress", "🟢 В работе" in msg2)
check("message manager", "Иван" in msg2)
kb2 = json.loads(build_order_keyboard(order))
labels = [btn["action"]["label"] for btn in kb2["buttons"][0]]
check("keyboard done/cancel", labels == ["✅ Завершено", "❌ Отказ"])

# --- Service with mocked VK ---
class FakeVK:
    def __init__(self) -> None:
        self.sent = []
        self.edited = []

    def send_order_message(self, order: Order) -> tuple[int, int]:
        self.sent.append(order.id)
        return 2000000100, 555

    def edit_order_message(self, order: Order) -> None:
        self.edited.append((order.id, order.status))


db = TestingSessionLocal()
vk = FakeVK()
service = OrderService(db, vk_client=vk)
created = service.create_order("Иван", 205, 55, 16, "+79991234567")
check("create order id", created.id is not None and created.id > 0)
check("create status NEW", created.status == OrderStatus.NEW)
check("vk message sent", vk.sent == [created.id])
check("vk meta saved", created.vk_message_id == 555 and created.vk_peer_id == 2000000100)

updated = service.update_status(created.id, OrderStatus.IN_PROGRESS, "Иван", 123)
check("take in progress", updated.status == OrderStatus.IN_PROGRESS)
check("manager saved", updated.manager_name == "Иван" and updated.manager_vk_id == 123)
check("vk edited", vk.edited[-1] == (created.id, OrderStatus.IN_PROGRESS))

done = service.update_status(created.id, OrderStatus.DONE)
check("done status", done.status == OrderStatus.DONE)

try:
    service.update_status(created.id, OrderStatus.IN_PROGRESS)
    check("cannot re-take done", False)
except ValueError:
    check("cannot re-take done", True)

# second order for cancel path
created2 = service.create_order("Петр", 215, 60, 16, "+79990001122")
service.update_status(created2.id, OrderStatus.IN_PROGRESS, "Петр", 456)
canceled = service.update_status(created2.id, OrderStatus.CANCELED)
check("canceled status", canceled.status == OrderStatus.CANCELED)

# --- HTTP API ---
# Patch OrderService VK inside endpoint by monkeypatching class used in route
from app.api import orders as orders_api


class ServiceWithFakeVK(OrderService):
    def __init__(self, db):
        super().__init__(db, vk_client=FakeVK())


orders_api.OrderService = ServiceWithFakeVK

health = client.get("/health")
check("GET /health", health.status_code == 200 and health.json()["status"] == "ok")

resp = client.post(
    "/api/orders",
    json={"name": "Иван", "width": 205, "profile": 55, "radius": 16, "phone": "+79991234567"},
)
check("POST /api/orders 201", resp.status_code == 201, f"got {resp.status_code} {resp.text}")
body = resp.json() if resp.status_code == 201 else {}
check("POST success true", body.get("success") is True, str(body))
check("POST order_id present", isinstance(body.get("order_id"), int), str(body))

bad = client.post(
    "/api/orders",
    json={"name": "Иван", "width": 10, "profile": 55, "radius": 16, "phone": "+79991234567"},
)
check("POST invalid width 422", bad.status_code == 422)

bad_phone = client.post(
    "/api/orders",
    json={"name": "Иван", "width": 205, "profile": 55, "radius": 16, "phone": "abc"},
)
check("POST invalid phone 422", bad_phone.status_code == 422)


class BrokenVK:
    def send_order_message(self, order: Order) -> tuple[int, int]:
        raise httpx.ProxyError("403 Forbidden")


class ServiceWithBrokenVK(OrderService):
    def __init__(self, db):
        super().__init__(db, vk_client=BrokenVK())


orders_api.OrderService = ServiceWithBrokenVK
vk_fail = client.post(
    "/api/orders",
    json={"name": "Иван", "width": 205, "profile": 55, "radius": 16, "phone": "+79993334455"},
)
check("POST VK failure 502", vk_fail.status_code == 502, f"got {vk_fail.status_code} {vk_fail.text}")
orders_api.OrderService = ServiceWithFakeVK

# --- Bot callback handler ---
sys.path.insert(0, str(BACKEND_DIR.parent / "vk-tire-bot"))
import order_handlers as oh
from order_handlers import handle_order_callback  # noqa: E402

# Patch SessionLocal and OrderService used by bot
oh.SessionLocal = TestingSessionLocal


class BotOrderService(OrderService):
    def __init__(self, db):
        super().__init__(db, vk_client=FakeVK())


oh.OrderService = BotOrderService

vk_api_mock = MagicMock()
vk_api_mock.users.get.return_value = [{"first_name": "Иван", "last_name": "Тестов"}]

# create fresh NEW order for callback
db2 = TestingSessionLocal()
svc2 = OrderService(db2, vk_client=FakeVK())
order_for_cb = svc2.create_order("Иван", 195, 65, 15, "+79001112233")
db2.close()

result = handle_order_callback(
    vk_api_mock,
    {
        "payload": {"order_id": order_for_cb.id, "action": "take"},
        "user_id": 999,
        "event_id": "evt",
        "peer_id": 2000000100,
    },
)
check("callback take text", f"Заявка №{order_for_cb.id} взята в работу" == result, result)

db3 = TestingSessionLocal()
reloaded = db3.get(Order, order_for_cb.id)
check("callback status IN_PROGRESS", reloaded is not None and reloaded.status == OrderStatus.IN_PROGRESS)
check("callback manager name", reloaded is not None and reloaded.manager_name == "Иван Тестов")
db3.close()

result_done = handle_order_callback(
    vk_api_mock,
    {
        "payload": json.dumps({"order_id": order_for_cb.id, "action": "done"}),
        "user_id": 999,
        "event_id": "evt2",
        "peer_id": 2000000100,
    },
)
check("callback done text", f"Заявка №{order_for_cb.id} завершена" == result_done, result_done)

# double take should fail gracefully
db4 = TestingSessionLocal()
svc4 = OrderService(db4, vk_client=FakeVK())
order_dup = svc4.create_order("Иван", 205, 55, 16, "+79991112233")
svc4.update_status(order_dup.id, OrderStatus.IN_PROGRESS, "А", 1)
db4.close()
result_dup = handle_order_callback(
    vk_api_mock,
    {
        "payload": {"order_id": order_dup.id, "action": "take"},
        "user_id": 1,
        "event_id": "evt3",
        "peer_id": 2000000100,
    },
)
check("callback double take blocked", result_dup == "Заявка уже взята в работу", result_dup)

print()
print(f"Result: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
