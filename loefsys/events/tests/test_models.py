from django.test import TestCase
from django_dynamic_fixture import G

from loefsys.events.models import Event, EventRegistration, MandatoryRegistrationDetails
from loefsys.events.models.event import EventOrganizer


class EventTestCase(TestCase):
    def test_create(self):
        event = G(Event)
        self.assertIsNotNone(event)
        self.assertIsNotNone(event.pk)


class MandatoryRegistrationDetailsTestCase(TestCase):
    def test_create(self):
        details = G(MandatoryRegistrationDetails)
        self.assertIsNotNone(details)
        self.assertIsNotNone(details.pk)


class EventOrganizerTestCase(TestCase):
    def test_create(self):
        organizer = G(EventOrganizer)
        self.assertIsNotNone(organizer)
        self.assertIsNotNone(organizer.pk)


class EventRegistrationTestCase(TestCase):
    def test_create(self):
        registration = G(EventRegistration)
        self.assertIsNotNone(registration)
        self.assertIsNotNone(registration.pk)
