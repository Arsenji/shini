import logging
import time

from fastapi import APIRouter, HTTPException, status

from app.config import get_settings
from app.schemas.order import OrderCreate, OrderCreateResponse
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate) -> OrderCreateResponse:
    settings = get_settings()
    if not settings.vk_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK не настроен: задайте VK_TOKEN и VK_PEER_ID (или VK_CHAT_ID) на сервере",
        )

    service = OrderService()
    try:
        service.create_order(
            name=payload.name,
            width=payload.width,
            profile=payload.profile,
            radius=payload.radius,
            phone=payload.phone,
        )
    except RuntimeError as error:
        logger.exception("VK API failure while creating order")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return OrderCreateResponse(order_id=int(time.time()))
