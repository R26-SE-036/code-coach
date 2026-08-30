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
    # Firestore database to use. "(default)" is the one created with the
    # project; set this to a named database when the default one sits in a
    # distant region (a database's location cannot be changed after creation,
    # and every round trip pays that distance).
    firebase_database_id: str = "(default)"

    mongodb_uri: Optional[str] = None
    mongodb_db_name: str = "code-guru"

    # Browser clients (the CodeGuru website, teammates' dev servers) need CORS.
    # Comma-separated origins; the VS Code extension is unaffected (Node fetch).
    # Example: CORS_ALLOWED_ORIGINS=http://localhost:3000,https://codeguru.example.com
    cors_allowed_origins: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://localhost:5174,http://localhost:4200"
    )

    # Brute-force protection: attempts allowed per client IP, per endpoint,
    # per window, on register/login/refresh. 10/min ≈ 14k guesses/day — far
    # too slow for password cracking, generous for real users.
    auth_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 60

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 7 * 24 * 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
