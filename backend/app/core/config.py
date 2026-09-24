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
    # 1. MongoDB   — set mongodb_uri
    # 2. In-memory — fallback for local development; data is LOST on restart
    #
    # `extra="ignore"` above means a stale variable left in an old .env is read
    # and discarded rather than rejected, so nothing breaks for anyone who has
    # not cleaned theirs up.
    mongodb_uri: Optional[str] = None
    mongodb_db_name: str = "code_coach"

    # Browser clients (the CodeGuru website, teammates' dev servers) need CORS.
    # Comma-separated origins; the VS Code extension is unaffected (Node fetch).
    # Example: CORS_ALLOWED_ORIGINS=http://localhost:3000,https://codeguru.example.com
    cors_allowed_origins: str = (
        "http://localhost:3000,http://localhost:5173,"
        "http://localhost:5174,http://localhost:4200"
    )

    # Brute-force protection on the credential endpoints, in two layers.
    #
    # Per ACCOUNT is what stops password guessing: 10 attempts a minute at one
    # account is ~14k guesses a day, far too slow for cracking.
    #
    # Per client IP used to be the only layer, at that same 10. But a class in a
    # lab reaches us from one address, so the eleventh student to sign in within
    # a minute was refused for their classmates' logins. The IP layer now only
    # has to stop one machine hammering many accounts, and is set for a room.
    auth_rate_limit_attempts: int = 60
    auth_account_rate_limit_attempts: int = 10
    auth_rate_limit_window_seconds: int = 60

    # ── Account recovery email ──
    # Reset and confirmation links point at the website. SMTP is Gmail in the
    # deployment (smtp.gmail.com, port 587, an app password); unset, no email
    # is sent and the service says so in its log. `mail_log_links` also prints
    # the link there - for local development only, never in a deployment.
    public_web_url: str = "http://localhost:4200"
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    mail_from: Optional[str] = None
    mail_log_links: bool = False
    password_reset_ttl_minutes: int = 30
    recovery_email_ttl_hours: int = 24
    # Reset emails per address per 15 minutes, so the form cannot be used to
    # flood someone's inbox.
    reset_emails_per_address: int = 3

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 7 * 24 * 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
