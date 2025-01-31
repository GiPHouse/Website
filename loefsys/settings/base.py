"""Module containing the base configuration."""

from collections.abc import Sequence
from pathlib import Path
from typing import cast

from cbs import BaseSettings as ClassySettings, env

denv = env["DJANGO_"]


class BaseSettings(ClassySettings):
    """Base class for settings configuration.

    The base class configures essential variables, such as the debug mode, which may be
    required by other modules.
    """

    BASE_DIR = Path(__file__).resolve(strict=True).parent.parent.parent

    DEBUG = denv.bool(False)
    ALLOWED_HOSTS = denv.list("")

    ROOT_URLCONF = "loefsys.urls"
    WSGI_APPLICATION = "loefsys.wsgi.application"

    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    @denv
    def SECRET_KEY(self) -> str:  # noqa N802 D102
        raise ValueError("Environment variable DJANGO_SECRET_KEY must be set.")

    def INTERNAL_IPS(self) -> Sequence[str]:  # noqa N802 D102
        return ("localhost", "127.0.0.1") if self.DEBUG else ()

    def DJANGO_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return ("django.contrib.contenttypes",)

    def THIRD_PARTY_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return ("debug_toolbar",) if self.DEBUG else ()

    def LOCAL_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return (
            "loefsys.events",
            "loefsys.groups",
            "loefsys.reservations",
            "loefsys.users",
        )

    def INSTALLED_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return (
            *cast(Sequence[str], self.DJANGO_APPS),
            *cast(Sequence[str], self.THIRD_PARTY_APPS),
            *cast(Sequence[str], self.LOCAL_APPS),
        )

    def MIDDLEWARE(self) -> Sequence[str]:  # noqa N802 D102
        return (
            ("debug_toolbar.middleware.DebugToolbarMiddleware",) if self.DEBUG else ()
        )
