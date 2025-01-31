"""Module containing the model for an event registration."""

from decimal import Decimal
from typing import Any

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import Case, F, When
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from .choices import RegistrationStatus
from .event import Event
from .managers import EventRegistrationManager


class EventRegistration(TimeStampedModel):
    """Registration model for an event.

    TODO @Mark expand on this.

    Attributes
    ----------
    created : ~datetime.datetime
        The timestamp of the creation of this model.
    modified : ~datetime.datetime
        The timestamp of last modification of this model.
    event : ~loefsys.events.models.event.Event
        The event to which the registration applies.
    contact : ~loefsys.contacts.models.Contact
        The contact that the registration is for.
    status : ~loefsys.events.models.choices.RegistrationStatus
        The status is active, in the queue, or cancelled, either with or without fine.
    price_at_registration : ~decimal.Decimal
        The agreed price of the event at the time of registration.
    fine_at_registration : ~decimal.Decimal
        The agreed fine for cancellation at the time of registration.
    costs : ~decimal.Decimal
        The cost for this event, automatically calculated from the status.
    costs_paid : ~decimal.Decimal
        The amount paid for this registration by the contact.
    """

    event = models.ForeignKey(Event, models.CASCADE)
    contact = models.ForeignKey(get_user_model(), models.SET_NULL, null=True)

    status = models.PositiveSmallIntegerField(
        choices=RegistrationStatus, blank=True, verbose_name=_("status")
    )

    price_at_registration = models.DecimalField(
        _("price"), max_digits=5, decimal_places=2, blank=True
    )
    fine_at_registration = models.DecimalField(
        _("fine"), max_digits=5, decimal_places=2, blank=True
    )
    costs = models.GeneratedField(
        expression=Case(
            When(status=RegistrationStatus.ACTIVE, then=F("price_at_registration")),
            When(
                status=RegistrationStatus.CANCELLED_FINE, then=F("fine_at_registration")
            ),
            default=Decimal("0.00"),
        ),
        output_field=models.DecimalField(max_digits=5, decimal_places=2),
        db_persist=True,
    )
    costs_paid = models.DecimalField(
        max_digits=5, decimal_places=2, verbose_name=_("costs paid")
    )

    objects = EventRegistrationManager()

    class Meta:
        unique_together = ("event", "contact")

    def __str__(self) -> str:
        return f"{self.event} | {self.contact}"

    def save(self, **kwargs: Any) -> None:
        """Save the model to the database.

        When creating a new registration, the attributes :attr:`.price_at_registration`
        and :attr:`.fine_at_registration` are copied from the :attr`.event`.

        Returns
        -------
        None
        """
        if self._state.adding:
            self.status = (
                RegistrationStatus.QUEUED
                if self.event.max_capacity_reached()
                else RegistrationStatus.ACTIVE
            )
            self.price_at_registration = self.event.price
            self.fine_at_registration = self.event.fine
        return super().save(**kwargs)

    def costs_to_pay(self) -> Decimal:
        """Calculate the amount needed to be paid by the registration contact.

        TODO see if this function can be converted into a GeneratedField as well.

        Returns
        -------
        ~decimal.Decimal
            The amount of money in Euro's.
        """
        return self.costs - self.costs_paid

    def cancel(self) -> None:
        """Cancel a registration.

        Upon cancellation, it is calculated whether a fine will be applied. The status
        of the registration is then either changed to
        :attr:`loefsys.events.models.choices.RegistrationStatus.CANCELLED_FINE` or
        :attr:`loefsys.events.models.choices.RegistrationStatus.CANCELLED_NOFINE`.
        Afterwards, the event is notified to potentially activate a registration in the
        queue.
        """
        if self.status in {
            RegistrationStatus.CANCELLED_FINE,
            RegistrationStatus.CANCELLED_NOFINE,
        }:
            return

        self.status = (
            RegistrationStatus.CANCELLED_FINE
            if self.event.fine_on_cancellation()
            and self.status == RegistrationStatus.ACTIVE
            else RegistrationStatus.CANCELLED_NOFINE
        )
        self.event.process_cancellation()
