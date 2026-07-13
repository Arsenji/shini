from functools import lru_cache

from pydantic import Field, field_validator
from pydantic.aliases import AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = "postgresql+psycopg://shini:shini@localhost:5432/shini"
    vk_token: str = ""
    vk_api_version: str = "5.199"
    vk_chat_id: str = ""
    # ID получателя в VK API (например, user_id менеджера для лички).
    # Если задан — используется вместо VK_CHAT_ID.
    vk_target_peer_id: str = Field(
        default="",
        validation_alias=AliasChoices("VK_TARGET_PEER_ID", "VK_PEER_ID"),
    )
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,https://shini-phi.vercel.app"

    @field_validator("vk_token", "vk_chat_id", "vk_target_peer_id", mode="before")
    @classmethod
    def strip_whitespace(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        if url.startswith("postgresql://") and "+psycopg" not in url:
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def vk_peer_id(self) -> int:
        # Приоритет: явный peer_id (например, user_id для личных сообщений),
        # иначе используем VK_CHAT_ID (id беседы без префикса 2000000000).
        if self.vk_target_peer_id:
            return int(self.vk_target_peer_id)

        chat_id = int(self.vk_chat_id)
        if chat_id >= 2_000_000_000:
            return chat_id
        return 2_000_000_000 + chat_id

    @property
    def vk_configured(self) -> bool:
        return bool(self.vk_token and (self.vk_target_peer_id or self.vk_chat_id))


@lru_cache
def get_settings() -> Settings:
    return Settings()
