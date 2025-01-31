"""Module defining models for reservable items."""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from ...users.models.choices import MembershipTypes
from .choices import Locations, ReservableCategories


class ReservableType(TimeStampedModel):
    """Model representing a type of reservable.

    This model exists to be able to make a collection of all reservables of the same
    type. Examples are wetsuits of the same size or the two 'valkjes' Scylla and
    Charybdis.

    Attributes
    ----------
    name : str
        The name of the type.
    category : ~loefsys.reservations.models.choices.ReservableCategories
        The category that the type falls under.
    description : str
        An additional description of the type.
    """

    name = models.CharField(max_length=40, verbose_name=_("Material type"), unique=True)
    category = models.PositiveSmallIntegerField(
        choices=ReservableCategories,
        default=ReservableCategories.OTHER,
        verbose_name=_("Reservable category"),
    )
    description = models.TextField(verbose_name=_("Type description"))

    def __str__(self) -> str:
        return self.name


class ReservableTypePricing(TimeStampedModel):
    """Pricing for the type of reservable.

    With this model, the pricing for a given ReservableType can be set for any
    membership defined by the Memberships enum.

    Attributes
    ----------
    reservable_type : ~loefsys.reservations.models.reservable.ReservableType
        The type for which the pricing is set.
    membership_type : ~loefsys.contacts.models.choices.MembershipTypes
        The membership type for which the pricing is set.
    price : ~decimal.Decimal
        The price in euro's.
    """

    reservable_type = models.OneToOneField(
        to=ReservableType, on_delete=models.CASCADE, verbose_name=_("Reservable type")
    )
    membership_type = models.PositiveSmallIntegerField(
        choices=MembershipTypes, verbose_name=_("Membership type")
    )
    price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(0)],
        verbose_name=_("Price"),
    )

    class Meta:
        unique_together = ("reservable_type", "membership_type")


class ReservableItem(TimeStampedModel):
    """The base model for a reservable item.

    A reservable item is an object that can be reserved. It can be set as
    non-reservable, for example due to maintenance. Additionally, it has a location and
    has a list of known complications.

    TODO add complications.

    Attributes
    ----------
    name : str
        The name of the item.
    description : str
        A description of the item.
    reservable_type : ~loefsys.reservations.models.reservable.ReservableType
        The type for which the pricing is set.
    location : ~loefsys.reservations.models.choices.Locations
        The location of the item.
    is_reservable : bool
        Flag to show availability.

        For example, if an item is unavailable due to maintenance, the value is set to
        `False`.
    """

    name = models.CharField(max_length=40, verbose_name=_("Name"))
    description = models.TextField(verbose_name=_("Description"))
    reservable_type = models.ForeignKey(
        ReservableType, on_delete=models.CASCADE, verbose_name=_("Reservable type")
    )
    location = models.PositiveSmallIntegerField(
        choices=Locations, default=Locations.OTHER, verbose_name=_("Location")
    )
    is_reservable = models.BooleanField(
        default=True,
        verbose_name=_("Reservable"),
        help_text=_(
            "When an item is unavailable for reservation, due to maintenance for "
            "example, set this to false."
        ),
    )

    class Meta:
        abstract = True
