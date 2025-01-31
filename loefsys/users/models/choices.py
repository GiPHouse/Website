"""Module containing all choice enums for the users app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class Genders(models.IntegerChoices):
    """Possible gender options for contacts."""

    OTHER = (0, _("Other"))
    """Used when other options don't apply."""

    UNSPECIFIED = (1, _("Prefer not to say"))
    """Used when the contact wants this information to remain private."""

    MALE = (2, _("Male"))
    """Used for male contacts."""

    FEMALE = (3, _("Female"))
    """Used for female contacts."""


class DisplayNamePreferences(models.IntegerChoices):
    """Possible options for displaying a person's name."""

    FULL = (0, _("Show full name"))
    """Used when the user wants their full name displayed."""

    FULL_WITH_NICKNAME = (1, _("Show full name with nickname"))
    """Used when the user wants their full name displayed, including nickname.

    For example: \"Willem-Alexander 'Willie' van Oranje\"
    """

    NICKNAME_LASTNAME = (2, _("Show the nickname and last name"))
    """Used for users who don't want their complete first name displayed."""

    INITIALS_LASTNAME = (3, _("Show only the initials and the last name"))
    """Used for users who want their initials and last name displayed."""

    FIRSTNAME_ONLY = (4, _("Show only the first name"))
    """Used when the user only wants their first name displayed."""

    NICKNAME_ONLY = (5, _("Show only the nickname"))
    """Used when the user only wants their nickname displayed."""


class MembershipTypes(models.IntegerChoices):
    """Possible options for membership of Loefbijter."""

    ACTIVE = (0, _("Active membership"))
    """Used when the person is an active member of Loefbijter."""

    PASSIVE = (1, _("Passive membership"))
    """Used when the person is a passive member of Loefbijter."""

    ACTIVE_EXCEPTIONAL = (2, _("Active exceptional membership"))
    """Used for a person who is 'buitengewoon lid' and is active."""

    PASSIVE_EXCEPTIONAL = (3, _("Passive exceptional membership"))
    """Used for a person who is 'buitengewoon lid' and is passive."""

    ALUMNUS = (4, _("Alumnus"))
    """Used when the person is an alumnus."""
