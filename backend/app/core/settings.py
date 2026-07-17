from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL

from app.common.constants import (
    API_V1_PREFIX_DEFAULT,
    APP_NAME_DEFAULT,
    APP_VERSION_DEFAULT,
)

Environment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="VNSTOCKLAB_",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = APP_NAME_DEFAULT
    app_version: str = APP_VERSION_DEFAULT
    environment: Environment = "development"
    debug: bool = False
    api_v1_prefix: str = API_V1_PREFIX_DEFAULT
    log_level: LogLevel = "INFO"
    allowed_hosts: list[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])
    database_host: str = "localhost"
    database_port: int = Field(default=5432, ge=1, le=65535)
    database_name: str = "vnstocklab"
    database_user: str = "vnstocklab"
    database_password: SecretStr = SecretStr("change-me-local-only")
    database_echo: bool = False
    database_pool_size: int = Field(default=5, ge=1)
    database_max_overflow: int = Field(default=10, ge=0)
    database_pool_timeout_seconds: int = Field(default=30, ge=1)

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.database_user,
            password=self.database_password.get_secret_value(),
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
