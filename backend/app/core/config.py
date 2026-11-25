from pathlib import Path
from typing import Literal

from pydantic import SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    app_name:str = "MyJARVIS"
    app_version: str = "0.1.0"
    environment: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    database_url: str
    database_echo: bool = False
    redis_url: str = "redis://127.0.0.1:6379/0"

    deepseek_api_key: SecretStr | None = None
    llm_base_url: str = "https://api.deepseek.com"
    llm_model_id: str = "deepseek-flash"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: object) -> object:
        return value.lower() if isinstance(value, str) else value

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value

settings = Settings()
