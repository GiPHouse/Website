"""Module containing all choice enums for the events app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class EventCategories(models.IntegerChoices):
    """Categories for an event.

    Events can be filtered based on their category. This enum is used for the
    filtering.
    """

    OTHER = (0, _("Other"))
    """Used when other categories aren't appropriate."""

    ALUMNI = (1, _("Alumni"))
    """Used for events for ex-members of the association."""

    ASSOCIATION = (2, _("Association"))
    """Used for events related to the board.

    Examples are general meetings, or the 'friettafelmoment'.
    """

    COMPETITION = (3, _("Competition"))
    """Used for events specifically for sailing competitions.

    Examples are NESTOR, regatta's, and more.
    """

    LEISURE = (4, _("Leisure"))
    """Used for entertainment events.

    Examples are 'borrels', parties, game activities, and more.
    """

    SAILING = (5, _("Sailing"))
    """Used for events directly involving sailing."""


class RegistrationStatus(models.IntegerChoices):
    """The various statuses for the registration."""

    ACTIVE = (0, _("Active"))
    """The registration is active and is neither cancelled nor queued."""

    QUEUED = (1, _("In queue"))
    """The registration is queued as the maximum capacity for the event is reached."""

    CANCELLED_NOFINE = (2, _("Cancelled"))
    """The registration is cancelled and no fine is applied."""

    CANCELLED_FINE = (3, _("Cancelled and fined"))
    """The registration is cancelled and a fine is applied."""
