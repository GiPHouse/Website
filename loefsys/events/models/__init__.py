"""Module containing the models related to events."""

from .event import Event, MandatoryRegistrationDetails
from .registration import EventRegistration

__all__ = ["Event", "EventRegistration", "MandatoryRegistrationDetails"]
