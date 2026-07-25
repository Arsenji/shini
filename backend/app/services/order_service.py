import logging
import random
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

MSK = ZoneInfo("Europe/Moscow")

CATEGORY_LABELS = {
    "passenger": "Легковые",
    "lcv": "Легкогрузовые",
    "truck": "Грузовые",
}

SEASON_LABELS = {
    "summer": "Лето",
    "winter": "Зима",
    "allseason": "Всесезон",
}


@dataclass
class OrderData:
    name: str
    width: int
    profile: int
    radius: float
    phone: str
    created_at: datetime
    size_label: str | None = None
    brand: str | None = None
    model: str | None = None
    category: str | None = None
    season: str | None = None
    sizes: str | None = None
    product_id: str | None = None

    @property
    def display_size(self) -> str:
        if self.size_label:
            return self.size_label
        radius = int(self.radius) if float(self.radius).is_integer() else self.radius
        return f"{self.width}/{self.profile} R{radius}"


def format_phone_display(phone: str) -> str:
    digits = "".join(ch for ch in phone if ch.isdigit())
    if len(digits) == 11 and digits.startswith("7"):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    return phone


def format_datetime(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=MSK)
    return dt.astimezone(MSK).strftime("%d.%m.%Y %H:%M")


def build_order_message(order: OrderData) -> str:
    lines = [
        "🚗 Новая заявка",
        "",
        "Имя:",
        "",
        order.name,
        "",
    ]

    if order.brand or order.model:
        lines.extend(
            [
                "Товар:",
                "",
                f"{order.brand or ''} {order.model or ''}".strip(),
                "",
            ]
        )

    if order.category:
        lines.extend(
            [
                "Тип:",
                "",
                CATEGORY_LABELS.get(order.category, order.category),
                "",
            ]
        )

    if order.season:
        lines.extend(
            [
                "Сезон:",
                "",
                SEASON_LABELS.get(order.season, order.season),
                "",
            ]
        )

    lines.extend(
        [
            "Размер:",
            "",
            order.display_size,
            "",
        ]
    )

    if order.sizes:
        lines.extend(
            [
                "Доступные размеры:",
                "",
                order.sizes,
                "",
            ]
        )

    lines.extend(
        [
            "Телефон:",
            "",
            format_phone_display(order.phone),
            "",
            "Время:",
            "",
            format_datetime(order.created_at),
        ]
    )

    return "\n".join(lines)


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

    def send_order_message(self, order: OrderData) -> None:
        self._post(
            "messages.send",
            {
                "peer_id": self.settings.vk_peer_id,
                "random_id": random.randint(1, 2_000_000_000),
                "message": build_order_message(order),
            },
        )


class OrderService:
    def __init__(self, vk_client: VKClient | None = None) -> None:
        self.vk = vk_client or VKClient()

    def create_order(
        self,
        name: str,
        width: int,
        profile: int,
        radius: float,
        phone: str,
        *,
        size_label: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        category: str | None = None,
        season: str | None = None,
        sizes: str | None = None,
        product_id: str | None = None,
    ) -> OrderData:
        order = OrderData(
            name=name,
            width=width,
            profile=profile,
            radius=radius,
            phone=phone,
            created_at=datetime.now(MSK),
            size_label=size_label,
            brand=brand,
            model=model,
            category=category,
            season=season,
            sizes=sizes,
            product_id=product_id,
        )
        logger.info(
            "Sending order to VK: product=%s size=%s phone=%s",
            f"{brand or ''} {model or ''}".strip() or "-",
            order.display_size,
            order.phone,
        )

        try:
            self.vk.send_order_message(order)
        except Exception as error:
            logger.exception("Failed to send VK message")
            raise RuntimeError("VK send failed") from error

        return order
