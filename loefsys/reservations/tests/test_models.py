from django.test import TestCase
from django_dynamic_fixture import G

from loefsys.reservations.models import Boat, Material, ReservableType


class BoatTestCase(TestCase):
    def test_create(self):
        boat = G(Boat)
        self.assertIsNotNone(boat)
        self.assertIsNotNone(boat.pk)


class MaterialTestCase(TestCase):
    def test_create(self):
        material = G(Material)
        self.assertIsNotNone(material)
        self.assertIsNotNone(material.pk)


class ReservableTypeTestCase(TestCase):
    def test_create(self):
        reservable_type = G(ReservableType)
        self.assertIsNotNone(reservable_type)
        self.assertIsNotNone(reservable_type.pk)


class ReservableTypePricingTestCase(TestCase):
    def test_create(self):
        pricing = G(ReservableType)
        self.assertIsNotNone(pricing)
        self.assertIsNotNone(pricing.pk)
