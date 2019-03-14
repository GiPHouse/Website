from django.test import TestCase
from django.contrib.auth.models import User
from datetime import datetime
from room_reservation.models import Room, Reservation
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

    def test_Reservation__str__(self):

        reservation = Reservation.objects.create(
            reservee=self.user,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        tz = get_current_timezone()
        start = reservation.start_time.astimezone(tz)
        end = reservation.end_time.astimezone(tz)
        start = start.strftime("%d/%m/%Y %H:%M")
        end = end.strftime("%d/%m/%Y %H:%M")

        self.assertEqual(str(reservation),
                         f"{reservation.reservee} has {reservation.room} reserved at {start} until {end}"
                         )
