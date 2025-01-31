"""Module containing the settings related to the admin interface."""

from collections.abc import Sequence

from .auth import AuthSettings
from .base import BaseSettings
from .templates import TemplateSettings


class AdminSettings(AuthSettings, TemplateSettings, BaseSettings):
    """Class defining the settings for the admin interface."""

    def DJANGO_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return (
            *super().DJANGO_APPS(),
            "django.contrib.messages",
            "django.contrib.admin",
        )

    def MIDDLEWARE(self) -> Sequence[str]:  # noqa N802 D102
        return (
            *super().MIDDLEWARE(),
            "django.contrib.messages.middleware.MessageMiddleware",
        )

    def templates_context_processors(self) -> Sequence[str]:  # noqa D102
        return (
            *super().templates_context_processors(),
            "django.contrib.messages.context_processors.messages",
        )
