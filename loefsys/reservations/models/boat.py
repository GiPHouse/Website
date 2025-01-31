"""Module defining the model for a boat that can be reserved."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import FleetChoices, ReservableCategories
from .reservable import ReservableItem, ReservableType


class Boat(ReservableItem):
    """Describes a boat that can be reserved.

    A boat is part of our or any external fleet of boats. It can be any type of boat. A
    boat requires a certain skipper's certificate. It has a limited can possibly and can
    possibly have an engine.

    Attributes
    ----------
    reservable_type : ~loefsys.reservations.models.reservable.ReservableType
        The type for which the pricing is set.
    capacity : int
        The capacity of the boat.
    has_engine : bool
        Flag that determines whether the boat has an engine.
    fleet : ~loefsys.reservations.models.choices.FleetChoices
        The provider of the boat.
    """

    reservable_type = models.ForeignKey(
        ReservableType,
        on_delete=models.CASCADE,
        verbose_name=_("Reservable type"),
        limit_choices_to={"category": ReservableCategories.BOAT},
    )
    capacity = models.PositiveSmallIntegerField(verbose_name=_("Capacity"))
    has_engine = models.BooleanField(
        default=False, verbose_name=_("Boat has an engine")
    )
    fleet = models.PositiveSmallIntegerField(
        choices=FleetChoices,
        default=FleetChoices.OTHER,
        verbose_name=_("Boat provider"),
    )
