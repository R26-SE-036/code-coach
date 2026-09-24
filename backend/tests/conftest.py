"""Shared test configuration.

The auth rate limit (10 attempts/min/IP in production) would trip the test
suite, which fires dozens of register/login calls from one fake client within
seconds. Raise it process-wide BEFORE any app import caches the settings.
The dedicated rate-limit tests install their own strict limiter explicitly.
"""

import os

os.environ.setdefault("AUTH_RATE_LIMIT_ATTEMPTS", "10000")
os.environ.setdefault("AUTH_ACCOUNT_RATE_LIMIT_ATTEMPTS", "10000")
os.environ.setdefault("RESET_EMAILS_PER_ADDRESS", "10000")
