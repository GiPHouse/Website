"""Module containing the settings for user authentication."""

from collections.abc import Sequence

from .base import BaseSettings
from .templates import TemplateSettings

DJANGO_PASSWORD_VALIDATION_MODULE = "django.contrib.auth.password_validation"


class AuthSettings(TemplateSettings, BaseSettings):
    """Class containing the settings for user authentication."""

    AUTH_USER_MODEL = "loefusers.User"

    # from: https://docs.djangoproject.com/en/5.0/topics/auth/passwords/#using-argon2-with-django
    PASSWORD_HASHERS = (
        "django.contrib.auth.hashers.Argon2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
        "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
        "django.contrib.auth.hashers.ScryptPasswordHasher",
    )

    AUTH_PASSWORD_VALIDATORS = (
        {
            "NAME": "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        },
        {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
        {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
        {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
    )

    def DJANGO_APPS(self) -> Sequence[str]:  # noqa N802
        return (
            *super().DJANGO_APPS(),
            "django.contrib.auth",
            "django.contrib.sessions",
        )

    def THIRD_PARTY_APPS(self) -> Sequence[str]:  # noqa N802
        return super().THIRD_PARTY_APPS()  # + ["allauth", "allauth.account"]

    def MIDDLEWARE(self) -> Sequence[str]:  # noqa N802
        return (
            *super().MIDDLEWARE(),
            "django.contrib.sessions.middleware.SessionMiddleware",
            "django.middleware.csrf.CsrfViewMiddleware",
            "django.contrib.auth.middleware.AuthenticationMiddleware",
        )

    def templates_context_processors(self) -> Sequence[str]:  # noqa D102
        return (
            *super().templates_context_processors(),
            "django.contrib.auth.context_processors.auth",
        )
