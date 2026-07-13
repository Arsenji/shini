import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.orders import router as orders_router
from app.config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

settings = get_settings()

app = FastAPI(title="КОЛЁСА ДЁШЕВО API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(orders_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
