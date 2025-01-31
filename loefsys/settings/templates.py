"""Module containing the configuration for templates."""

from collections.abc import Sequence


class TemplateSettings:
    """Class containing the configuration for templates."""

    def TEMPLATES(self) -> Sequence[dict]:  # noqa N802 D102
        return (
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "APP_DIRS": True,
                "OPTIONS": {"context_processors": self.templates_context_processors()},
            },
        )

    def templates_context_processors(self) -> Sequence[str]:  # noqa D102
        return (
            "django.template.context_processors.debug",
            "django.template.context_processors.request",
        )
