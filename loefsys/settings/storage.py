"""Module containing the configuration for media storage."""

from collections.abc import Sequence
from pathlib import Path

from cbs import env

from .base import BaseSettings
from .templates import TemplateSettings


class StorageSettings(TemplateSettings, BaseSettings):
    """Class containing the configuration for media storage."""

    AWS_STORAGE_BUCKET_NAME = env(None)

    def uses_local_storage(self) -> bool:  # noqa N802 D102
        return self.DEBUG or not self.AWS_STORAGE_BUCKET_NAME

    def AWS_S3_CUSTOM_DOMAIN(self) -> str:  # noqa N802 D102
        return f"{self.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com"

    def STATIC_URL(self) -> str:  # noqa N802 D102
        return (
            "static/"
            if self.uses_local_storage()
            else f"https://{self.AWS_S3_CUSTOM_DOMAIN}/static/"
        )

    def MEDIA_URL(self) -> str:  # noqa N802 D102
        return (
            "media/"
            if self.uses_local_storage()
            else f"https://{self.AWS_S3_CUSTOM_DOMAIN}/media/"
        )

    def STATIC_DIR(self) -> Path:  # noqa N802 D102
        return self.BASE_DIR / "staticfiles"

    def MEDIA_DIR(self):  # noqa N802 D102
        return self.BASE_DIR / "mediafiles"

    def DJANGO_APPS(self) -> Sequence[str]:  # noqa N802 D102
        return *super().DJANGO_APPS(), "django.contrib.staticfiles"

    def STORAGES(self) -> dict:  # noqa N802 D102
        return {
            "default": {
                "BACKEND": "storages.backends.s3boto3.S3Boto3Storage"
                if self.AWS_STORAGE_BUCKET_NAME
                else "django.core.files.storage.FileSystemStorage"
            },
            "staticfiles": {
                "BACKEND": "storages.backends.s3boto3.S3StaticStorage"
                if self.AWS_STORAGE_BUCKET_NAME
                else "django.contrib.staticfiles.storage.StaticFilesStorage"
            },
        }

    def templates_context_processors(self) -> Sequence[str]:  # noqa D102
        return (
            *super().templates_context_processors(),
            "django.template.context_processors.media",
            "django.template.context_processors.static",
        )
