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

    vk_token: str = ""
    vk_api_version: str = "5.199"
    vk_chat_id: str = ""
    # Получатели заявок. Можно несколько через запятую:
    #   VK_PEER_ID=146507806,225909038
    # Для беседы — один peer_id вида 2000000197 (если сообщество реально видит чат).
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
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def vk_peer_ids(self) -> list[int]:
        """Список peer_id для отправки заявки (ЛС и/или беседы)."""
        if self.vk_target_peer_id:
            ids: list[int] = []
            for part in self.vk_target_peer_id.replace(";", ",").split(","):
                part = part.strip()
                if not part:
                    continue
                ids.append(int(part))
            if ids:
                return ids

        if not self.vk_chat_id:
            return []

        chat_id = int(self.vk_chat_id)
        if chat_id >= 2_000_000_000:
            return [chat_id]
        return [2_000_000_000 + chat_id]

    @property
    def vk_peer_id(self) -> int:
        """Первый получатель (для обратной совместимости)."""
        ids = self.vk_peer_ids
        if not ids:
            raise ValueError("Не задан VK_PEER_ID или VK_CHAT_ID")
        return ids[0]

    @property
    def vk_configured(self) -> bool:
        return bool(self.vk_token and self.vk_peer_ids)


@lru_cache
def get_settings() -> Settings:
    return Settings()
