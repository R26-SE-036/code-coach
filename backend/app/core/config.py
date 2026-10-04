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

    # ── Research collection of analysed code ──
    # Off until the ethics application is approved. While off, students can
    # still record a decision, but no code is kept whatever they chose. On, it
    # keeps the code of students whose latest decision is GRANTED under the
    # current consent version (core/research_consent.py).
    #
    # The salt turns an account id into the participant code stored beside
    # the file. It must be secret, long and never change: a new salt makes
    # one student look like two. Collection stays off while it is unset.
    research_collection_enabled: bool = False
    research_id_salt: Optional[str] = None
    # Files larger than this are not kept - a paste of something that is not a
    # student's program, and not what the detector is trained on.
    research_max_code_chars: int = 50_000

    # ── Calls from other Code Guru services ──
    # PairPath asks which concepts a free-coding pair's code touches, so its
    # hints can find the right course notes. That call is server to server and
    # carries no student token, so it proves itself with this key instead - the
    # same value PairPath holds. Unset, the route refuses every call and
    # PairPath falls back to general teamwork nudges.
    internal_service_key: Optional[str] = None

    # ── Subscriptions (Free / Pro) ──
    # Code Coach owns who has Pro, because every other part of the platform
    # already asks it who the student is. See app/services/billing_service.py.
    #
    # PayHere is the gateway (Stripe does not take Sri Lankan merchants). The
    # merchant secret is the one PayHere issues for the site's domain; it signs
    # the checkout and verifies the payment notification. The app id/secret
    # are the Merchant API key, used only to cancel a recurring subscription
    # at PayHere - without them Cancel still works, on our side only.
    payhere_merchant_id: Optional[str] = None
    payhere_merchant_secret: Optional[str] = None
    payhere_app_id: Optional[str] = None
    payhere_app_secret: Optional[str] = None
    # The sandbox until there is a real merchant account. No real money moves.
    payhere_sandbox: bool = True
    pro_price_lkr: int = 490
    # Free students may open this many Study Guider lessons per month.
    free_lessons_per_month: int = 3
    # Turns on the no-card "demo payment" and the self-service reset back to
    # Free. For the viva (a backup when the gateway or the network fails) and
    # local development, where PayHere cannot reach the notify URL. Anyone
    # signed in can give themselves Pro while it is on, so it is off by default.
    billing_demo_mode: bool = False

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_seconds: int = 3600
    refresh_token_ttl_seconds: int = 7 * 24 * 3600


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
