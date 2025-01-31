"""Module defining the configuration for various security parameters."""

from collections.abc import Sequence

from .auth import AuthSettings
from .base import BaseSettings


class SecuritySettings(AuthSettings, BaseSettings):
    """Class defining the configuration for various security parameters."""

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True

    # TODO: set this to 60 seconds first and then to 518400 once you prove the former
    #  works
    SECURE_HSTS_SECONDS = 60
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    def MIDDLEWARE(self) -> Sequence[str]:  # noqa N802
        return (
            "django.middleware.security.SecurityMiddleware",
            "django.middleware.clickjacking.XFrameOptionsMiddleware",
            *super().MIDDLEWARE(),
        )
