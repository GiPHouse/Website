"""Module defining the room reservable model."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import ReservableCategories
from .reservable import ReservableItem, ReservableType


class Room(ReservableItem):
    """Model defining a room that can be reserved.

    A room is a place the Loefbijter owns which can be used by any part within
    Loefbijter (this does not include the VvS). It has a limited capacity and has
    required permission.

    Attributes
    ----------
    reservable_type : ~loefsys.reservations.models.reservable.ReservableType
        The type for which the pricing is set.
    name : str
        The name of the room.
    capacity : int
        The capacity of the room.
    """

    reservable_type = models.ForeignKey(
        ReservableType,
        on_delete=models.CASCADE,
        verbose_name=_("Reservable type"),
        limit_choices_to={"category": ReservableCategories.ROOM},
    )
    name = models.CharField(max_length=40, verbose_name=_("Room name"), unique=True)
    capacity = models.PositiveSmallIntegerField(verbose_name=_("Capacity"))
