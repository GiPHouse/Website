from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from room_reservation.models import Reservation, Room

User = get_user_model()


class ReservationTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.user = User.objects.create_user(
            username='myself',
            password='123',
        )

        cls.other_user = User.objects.create_user(
            username='someone else',
            password='123',
        )

        cls.room = Room.objects.create(
            name="New York",
            location="Merc 0.1337",
        )

        cls.user_reservation = Reservation.objects.create(
            reservee=cls.user,
            room=cls.room,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )

        cls.other_reservation = Reservation.objects.create(
            reservee=cls.other_user,
            room=cls.room,
            start_time=timezone.now(),
            end_time=timezone.now() + timezone.timedelta(hours=1),
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_get_calendar(self):
        response = self.client.get(reverse('room_reservation:calendar'))
        self.assertEqual(response.status_code, 200)
