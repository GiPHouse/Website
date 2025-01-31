"""In this module, the models for events are defined."""

from decimal import Decimal
from typing import Optional

from django.contrib.auth import get_user_model
from django.core import validators
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from loefsys.events.models.choices import EventCategories, RegistrationStatus
from loefsys.events.models.managers import EventManager, EventRegistrationManager
from loefsys.groups.models import LoefbijterGroup


class Event(TitleSlugDescriptionModel, TimeStampedModel):
    """Model for an event.

    TODO @Mark expand on this.

    Attributes
    ----------
    created : ~datetime.datetime
        The timestamp of the creation of the model, automatically generated upon
        creation.
    modified : ~datetime.datetime
        The timestamp of last modification of this model, automatically generated upon
        update.
    title : str
        The title to display for the event.
    description : str, None
        An optional description of the event.
    slug : str
        A slug for the URL of the event, automatically generated from the title.
    start : ~datetime.datetime
        The start date and time of the event.
    end : ~datetime.datetime
        The end date and time of the event.
    category : ~loefsys.events.models.choices.EventCategories
        The category of the event.
    price : ~decimal.Decimal
        The price.
    location : str
        The location of the event.

        We might want to include a Google Maps widget showing the location.
        `django-google-maps <https://pypi.org/project/django-google-maps/>`_ might be
        useful for this.
    is_open_event : bool
        Flag to determine if non-members can register.
    published : bool
        Flag to determine if the event is publicly visible.
    eventregistration_set : ~loefsys.events.models.managers.EventRegistrationManager
        A manager of registrations for this event.

        It is the one-to-many relationship to
        :class:`~loefsys.events.models.EventRegistration`.
    """

    start = models.DateTimeField(_("start time"))
    end = models.DateTimeField(_("end time"))

    category = models.PositiveSmallIntegerField(
        choices=EventCategories, verbose_name=_("category")
    )

    price = models.DecimalField(
        _("price"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        validators=[validators.MinValueValidator(0)],
    )
    fine = models.DecimalField(
        _("fine"),
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        blank=True,
        help_text=_("Fine if participant does not show up."),
        validators=[validators.MinValueValidator(0)],
    )

    location = models.CharField(_("location"), max_length=255)

    is_open_event = models.BooleanField(
        help_text=_("Event is open for non-members"), default=False
    )
    published = models.BooleanField(_("published"), default=False)

    registration_details: Optional["MandatoryRegistrationDetails"]
    eventregistration_set: EventRegistrationManager

    objects = EventManager()

    def __str__(self):
        return f"{self.__class__.__name__} {self.title}"

    def mandatory_registration(self) -> bool:
        """Check whether this event has mandatory registration.

        Returns
        -------
        bool
            A boolean that defines whether registration is mandatory.
        """
        return hasattr(self, "registration_details")

    def registrations_open(self) -> bool:
        """Determine whether it is possible for users to register for this event.

        Returns
        -------
        bool
            A boolean that defines whether registrations are open.
        """
        if not self.published:
            return False
        return (
            self.registration_details.registration_window_open()
            if hasattr(self, "registration_details")
            else timezone.now() < self.end
        )

    def max_capacity_reached(self) -> bool:
        """Check whether the max capacity for this event is reached.

        Returns
        -------
        bool
            ``True`` when the event is full and ``False`` if there are places available.
        """
        return (
            self.registration_details.capacity_reached()
            if self.mandatory_registration()
            else False
        )

    def fine_on_cancellation(self) -> bool:
        """Check whether the cancellation of a registration will result in a fine.

        Returns
        -------
        bool
            ``True`` when a fine will be applied and ``False`` when cancellation is
            free of charge.
        """
        if not self.mandatory_registration():
            return True
        deadline = self.registration_details.cancel_deadline or self.start
        return deadline < timezone.now()

    def process_cancellation(self) -> None:
        """Process the side effects for an event of a cancellation.

        Returns
        -------
        None
        """
        if not self.mandatory_registration():
            return

        num_active = self.eventregistration_set.active().count()
        num_queued = self.eventregistration_set.queued().count()
        if not num_queued or num_active >= self.registration_details.capacity:
            return

        num_available = self.registration_details.capacity - num_active
        num_to_add = min(num_available, num_queued)
        objs = self.eventregistration_set.queued().order_by_creation()[:num_to_add]
        modified = timezone.now()
        for obj in objs:
            obj.status = RegistrationStatus.ACTIVE
            obj.modified = modified
        # As save() isn't called on the objects, we manually update the field modified.
        self.eventregistration_set.bulk_update(objs, ["status", "modified"])


class MandatoryRegistrationDetails(TimeStampedModel):
    """Model containing extra information for an event that requires registration.

    Attributes
    ----------
    event : ~loefsys.events.models.event.Event
        The event that requires these details.
    start : ~datetime.datetime
        The opening of the registration window.
    end : ~datetime.datetime
        The closing of the registration window.
    cancel_deadline : ~datetime.datetime or None
        The deadline until which registration can be cancelled free of charge.
    send_cancel_email : bool
        Flag that shows whether people receive a confirmation email upon cancellation.
    capacity : int or None
        The capacity for the event, or `None` if there is no capacity.
    """

    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name="registration_details",
        verbose_name=_("event"),
    )

    start = models.DateTimeField(
        _("registration start"),
        help_text=_(
            "Prefer times when people don't have lectures, "
            "e.g. 12:30 instead of 13:37."
        ),
    )
    end = models.DateTimeField(
        _("registration end"),
        help_text=_(
            "If you set a registration period registration will be "
            "required. If you don't set one, registration won't be "
            "required."
        ),
    )

    cancel_deadline = models.DateTimeField(_("cancel deadline"), null=True, blank=True)
    send_cancel_email = models.BooleanField(
        _("send cancellation notifications"),
        default=True,
        help_text=_(
            "Send an email to the organising party when a member "
            "cancels their registration after the deadline."
        ),
    )

    capacity = models.PositiveSmallIntegerField(
        _("maximum number of participants"), blank=True, null=True
    )

    def registration_window_open(self) -> bool:
        """Determine whether it is possible for users to register for this event.

        For events with required registration, registration is only possible when the
        event is published and in the registration window defined by
        :attr:`.start` and :attr:`.end`.

        Returns
        -------
        bool
            A boolean that defines whether registrations are in the registration window.
        """
        return self.start < timezone.now() < self.end

    def capacity_reached(self) -> bool:
        """Determine whether the maximum capacity for the event has been reached.

        Returns
        -------
        bool
            A boolean that defines whether the capacity has been reached.
        """
        return (
            self.capacity is not None
            and self.capacity <= self.event.eventregistration_set.active().count()
        )


class EventOrganizer(TimeStampedModel):
    """Utility model collecting the organizers for an event.

    Attributes
    ----------
    created : ~datetime.datetime
        The timestamp of the creation of the model, automatically generated upon
        creation.
    modified : ~datetime.datetime
        The timestamp of last modification of this model, automatically generated upon
        update.
    event : ~loefsys.events.models.event.Event
        The event that the current organizer organizes.
    groups : ~django.db.models.query.QuerySet of ~loefsys.groups.models.LoefbijterGroup
        The groups organizing this event.
    contacts : ~django.db.models.query.QuerySet of ~loefsys.contacts.models.Contact
        Additional individuals organizing this event.
    """

    event = models.OneToOneField(
        Event, on_delete=models.CASCADE, verbose_name=_("event")
    )

    groups = models.ManyToManyField(
        to=LoefbijterGroup, related_name="events_organizer", blank=True
    )
    contacts = models.ManyToManyField(
        to=get_user_model(), related_name="events_contact"
    )
