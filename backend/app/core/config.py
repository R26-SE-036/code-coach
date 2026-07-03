from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

# loads environment variables
# gives app-wide settings



class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongodb_uri: Optional[str] = None
    mongodb_db_name: str = "code-guru"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 7 * 24 * 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
