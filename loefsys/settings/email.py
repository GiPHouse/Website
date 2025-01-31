"""Module containing the configuration for the email service."""


class EmailSettings:
    """Class containing the configuration for the email service."""

    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_TIMEOUT = 5

    DEFAULT_FROM_EMAIL = "Loefbijter <noreply@loefbijter.nl>"
    EMAIL_SUBJECT_PREFIX = "[Loefbijter]"

    def SERVER_EMAIL(self) -> str:  # noqa N802 D102
        return self.DEFAULT_FROM_EMAIL
