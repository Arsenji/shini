import re
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Только безопасный набор символов до нормализации (цифры, +, скобки, пробел, дефис)
PHONE_INPUT_PATTERN = re.compile(r"^[\d+\s\-()]+$")


def normalize_phone(value: str) -> str:
    if len(value) > 32:
        raise ValueError("Слишком длинный номер телефона")
    if not PHONE_INPUT_PATTERN.fullmatch(value):
        raise ValueError("Укажите корректный российский номер телефона")

    digits = re.sub(r"\D", "", value)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        return f"+{digits}"
    raise ValueError("Укажите корректный российский номер телефона")


class OrderCreate(BaseModel):
    width: Annotated[int, Field(ge=100, le=395)]
    profile: Annotated[int, Field(ge=20, le=95)]
    radius: Annotated[int, Field(ge=10, le=30)]
    phone: Annotated[str, Field(min_length=10, max_length=32)]

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value.strip())


class OrderCreateResponse(BaseModel):
    success: bool = True
    order_id: int
