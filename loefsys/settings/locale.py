"""Module containing the configuration for the localization."""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

from cbs import env

from .auth import AuthSettings
from .base import BaseSettings
from .templates import TemplateSettings

denv = env["DJANGO_"]


class LocaleSettings(AuthSettings, TemplateSettings, BaseSettings):
    """Class containing the configuration for the localization."""

    TIME_ZONE = denv("Europe/Amsterdam")
    LANGUAGE_CODE = "en-us"
    USE_I18N = True
    USE_TZ = True

    def LOCALE_DIR(self) -> Path:  # noqa N802 D102
        return self.BASE_DIR / "locale"

    def LOCALE_PATHS(self) -> Sequence[Path]:  # noqa N802 D102
        return (cast(Path, self.LOCALE_DIR),)

    def MIDDLEWARE(self) -> Sequence[str]:  # noqa N802 D102
        return *super().MIDDLEWARE(), "django.middleware.locale.LocaleMiddleware"

    def templates_context_processors(self) -> Sequence[str]:  # noqa D102
        return (
            *super().templates_context_processors(),
            "django.template.context_processors.i18n",
            "django.template.context_processors.tz",
        )
