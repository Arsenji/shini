from functools import lru_cache

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
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,https://shini-phi.vercel.app"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def vk_peer_id(self) -> int:
        return 2_000_000_000 + int(self.vk_chat_id)


@lru_cache
def get_settings() -> Settings:
    return Settings()
