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

    # Storage backend selection (checked in this order by build_storage):
    # 1. Firestore — set firebase_credentials_path to a service account key
    # 2. MongoDB   — set mongodb_uri
    # 3. In-memory — fallback for local development; data is LOST on restart
    firebase_credentials_path: Optional[str] = None
    firebase_project_id: Optional[str] = None

    mongodb_uri: Optional[str] = None
    mongodb_db_name: str = "code-guru"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 7 * 24 * 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
