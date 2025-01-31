"""Module containing enums for choice fields in the models for groups."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class FraternityGenders(models.IntegerChoices):
    """The possible type of the fraternity.

    Fraternities are typically divided into three categories: male-only, female-only,
    and mixed.
    """

    MIXED = 0, _("Mixed")
    """Used for mixed-gender fraternities."""

    FEMALE = 1, _("Female")
    """Used for female-only fraternities."""

    MALE = 2, _("Male")
    """Used for male-only fraternities."""
