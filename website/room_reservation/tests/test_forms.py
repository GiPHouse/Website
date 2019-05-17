from datetime import datetime

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.utils.timezone import get_current_timezone

from room_reservation.forms import ReservationForm
from room_reservation.models import Reservation, Room

User = get_user_model()


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
            'start_time': "2005-7-13 12:00",
            'end_time': "2005-7-14 12:00",
        }
        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_ReservationForm_out_of_range(self):
        form_data = {
            'room': str(self.room.pk),
            'start_time': "2005-7-14 6:00",
            'end_time': "2005-7-14 10:00",
        }
        form = ReservationForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_ReservationForm_end_time_past_start_time(self):
        form_data = {
            'room': str(self.room.pk),
            'start_time': "2005-7-13 12:30",
            'end_time': "2005-7-13 12:00",
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
