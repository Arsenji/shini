"""Tests for order API (VK mocked, без базы данных)."""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

os.environ["VK_TOKEN"] = "test-token"
os.environ["VK_PEER_ID"] = "123456789"
os.environ["CORS_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import get_settings
from app.main import app
from app.schemas.order import OrderCreate, normalize_phone
from app.services.order_service import OrderData, OrderService, build_order_message

get_settings.cache_clear()
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

ok = OrderCreate(
    name="Иван",
    width=205,
    profile=55,
    radius=16,
    phone="8 (999) 123-45-67",
    personal_data_consent=True,
)
check("valid OrderCreate", ok.phone == "+79991234567" and ok.personal_data_consent is True)

try:
    OrderCreate(name="Иван", width=205, profile=55, radius=16, phone="+79991234567")
    check("consent missing rejected", False)
except ValidationError:
    check("consent missing rejected", True)

try:
    OrderCreate(
        name="Иван",
        width=205,
        profile=55,
        radius=16,
        phone="+79991234567",
        personal_data_consent=False,
    )
    check("consent false rejected", False)
except ValidationError:
    check("consent false rejected", True)

order = OrderData(
    name="Иван",
    width=205,
    profile=55,
    radius=16,
    phone="+79991234567",
    created_at=datetime(2026, 8, 16, 17, 30),
    personal_data_consent=True,
    personal_data_consent_at=datetime(2026, 8, 16, 17, 30),
)
msg = build_order_message(order)
check("message has title", "🚗 Новая заявка" in msg)
check("message has name", "Иван" in msg)
check("message has size", "205/55 R16" in msg)
check("message has phone", "+7 (999) 123-45-67" in msg)
check("message has no status", "Статус" not in msg)
check("message has consent", "Согласие на обработку ПД: получено" in msg)
check("message has consent time", "Время согласия: 16.08.2026 17:30" in msg)

order_with_product = OrderData(
    name="Иван",
    width=185,
    profile=75,
    radius=16,
    phone="+79991234567",
    created_at=datetime(2026, 7, 13, 17, 45),
    size_label="185/75R16C",
    brand="Кама",
    model="НК-243",
    category="lcv",
    sizes="185/75R16C",
    product_id="kama-nk243-185-75r16c",
)
product_msg = build_order_message(order_with_product)
check("message has product", "Кама НК-243" in product_msg)
check("message has category", "Легкогрузовые" in product_msg)
check("message has size label", "185/75R16C" in product_msg)


class FakeVK:
    def __init__(self) -> None:
        self.sent = 0

    def send_order_message(self, order: OrderData) -> None:
        self.sent += 1


service = OrderService(vk_client=FakeVK())
created = service.create_order(
    "Иван",
    205,
    55,
    16,
    "+79991234567",
    personal_data_consent=True,
)
check("service returns order", created.name == "Иван")
check("vk message sent", service.vk.sent == 1)
check("service stores consent", created.personal_data_consent is True)


class BrokenVK:
    def send_order_message(self, order: OrderData) -> None:
        raise RuntimeError("VK API error: test")


try:
    OrderService(vk_client=BrokenVK()).create_order(
        "Иван",
        205,
        55,
        16,
        "+79991234567",
        personal_data_consent=True,
    )
    check("vk failure raises", False)
except RuntimeError:
    check("vk failure raises", True)


from app.api import orders as orders_api


class ServiceWithFakeVK(OrderService):
    def __init__(self) -> None:
        super().__init__(vk_client=FakeVK())


orders_api.OrderService = ServiceWithFakeVK

health = client.get("/health")
check("GET /health", health.status_code == 200 and health.json()["status"] == "ok")

resp = client.post(
    "/api/orders",
    json={
        "name": "Иван",
        "width": 205,
        "profile": 55,
        "radius": 16,
        "phone": "+79991234567",
        "personal_data_consent": True,
    },
)
check("POST /api/orders 201", resp.status_code == 201, f"got {resp.status_code} {resp.text}")
body = resp.json() if resp.status_code == 201 else {}
check("POST success true", body.get("success") is True, str(body))

missing_consent = client.post(
    "/api/orders",
    json={"name": "Иван", "width": 205, "profile": 55, "radius": 16, "phone": "+79991234567"},
)
check("POST without consent 422", missing_consent.status_code == 422)

false_consent = client.post(
    "/api/orders",
    json={
        "name": "Иван",
        "width": 205,
        "profile": 55,
        "radius": 16,
        "phone": "+79991234567",
        "personal_data_consent": False,
    },
)
check("POST consent false 422", false_consent.status_code == 422)

bad = client.post(
    "/api/orders",
    json={
        "name": "Иван",
        "width": 10,
        "profile": 55,
        "radius": 16,
        "phone": "+79991234567",
        "personal_data_consent": True,
    },
)
check("POST invalid width 422", bad.status_code == 422)


class ServiceWithBrokenVK(OrderService):
    def __init__(self) -> None:
        super().__init__(vk_client=BrokenVK())


orders_api.OrderService = ServiceWithBrokenVK
vk_fail = client.post(
    "/api/orders",
    json={
        "name": "Иван",
        "width": 205,
        "profile": 55,
        "radius": 16,
        "phone": "+79993334455",
        "personal_data_consent": True,
    },
)
check("POST VK failure 502", vk_fail.status_code == 502, f"got {vk_fail.status_code} {vk_fail.text}")

print(f"\nResult: {passed} passed, {failed} failed")
raise SystemExit(1 if failed else 0)
