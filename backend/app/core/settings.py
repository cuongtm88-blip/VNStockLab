from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VNSTOCKLAB_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "VNStockLab API"
    app_version: str = "1.0.0"
    environment: Environment = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: LogLevel = "INFO"
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])


@lru_cache
def get_settings() -> Settings:
    return Settings()
