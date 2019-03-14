from django.test import TestCase, Client
from django.contrib.auth.models import User
from datetime import datetime
from room_reservation.models import Room, Reservation
from room_reservation.forms import ReservationForm
from django.utils.timezone import get_current_timezone


class PeerReviewTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='myself',
            password='123',
        )

        cls.room = Room.objects.create(
            name="New York",
            location="Merc 0.1337",
        )
        cls.tz = get_current_timezone()

    def setUp(self):
        self.client = Client()
        self.client.login(username='myself', password='123')

    def test_ReservationForm_success(self):
        form_data = {
            'room': str(self.room.pk),
            'start_time': "2000-12-01 12:00",
            'end_time': "2000-12-01 13:00",
        }
        form = ReservationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_ReservationForm_too_long(self):
        form_data = {
            'room': str(self.room.pk),
            'start_time': "2005-7-14 5:00",
            'end_time': "2005-7-14 23:00",
        }
        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_ReservationForm_collision(self):

        Reservation.objects.create(
            reservee=self.user,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        form_data = {
            'room': str(self.room.pk),
            'start_time': "2005-7-14 12:00",
            'end_time': "2005-7-14 14:00",
        }
        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())
