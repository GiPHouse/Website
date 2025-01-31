"""Module containing the choice enums of the reservations app."""

from django.db import models
from django.utils.translation import gettext_lazy as _


class ReservableCategories(models.IntegerChoices):
    """The various categories that reservables are part of."""

    OTHER = (0, _("Other"))
    """Used for types that do not fall under the other categories."""

    BOAT = (1, _("Boat"))
    """Used for boat types."""

    ROOM = (2, _("Room"))
    """Used for room types."""

    MATERIAL = (3, _("Material"))
    """Used for material types."""


class Locations(models.IntegerChoices):
    """Locations where a reservable can be retrieved."""

    OTHER = (0, _("Other"))
    """Used when the other locations aren't applicable."""

    BOARDROOM = (1, _("Boardroom"))
    """Used when an item is located in the boardroom."""

    BASTION = (2, _("Bastion"))
    """Used when an item is located at the Bastion."""

    KRAAIJ = (3, _("Kraaijenbergse Plassen"))
    """Used when an item is located at the Kraaijenbergse Plassen."""


class FleetChoices(models.IntegerChoices):
    """Choices for the fleet."""

    OTHER = (0, _("Other"))
    """Used for boats available from other providers."""

    LOEFBIJTER = (1, _("Loefbijter"))
    """Used for boats from Loefbijter."""

    CEULEMANS = (2, _("Ceulemans"))
    """Used for boats from Ceulemans."""
