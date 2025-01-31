"""Module containing the settings definition for tests."""

from typing import ClassVar


class TestSettings:
    """Class containing the settings for testing."""

    DDF_IGNORE_FIELDS = ("display_name",)
    DDF_FIELD_FIXTURES: ClassVar[dict] = {
        "django.db.models.fields.generated.GeneratedField": lambda: None
    }
