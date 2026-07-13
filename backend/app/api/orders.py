import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.schemas.order import OrderCreate, OrderCreateResponse
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)) -> OrderCreateResponse:
    settings = get_settings()
    if not settings.vk_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="VK не настроен: задайте VK_TOKEN и VK_CHAT_ID на сервере",
        )

    service = OrderService(db)
    try:
        order = service.create_order(
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
    except Exception as error:
        logger.exception("Database failure while creating order")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ошибка сохранения заявки",
        ) from error

    return OrderCreateResponse(order_id=order.id)
