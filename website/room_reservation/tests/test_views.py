from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from room_reservation.models import Room, Reservation
from datetime import datetime
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

    def test_get_calendar(self):
        """
        Test GET request to the week calendar.
        """
        response = self.client.get(reverse('room_reservation:calendar'))
        self.assertEqual(response.status_code, 200)

    def test_get_create_reservation(self):
        """
        Test GET request to create reservation form.
        """
        response = self.client.get(
            reverse('room_reservation:create_reservation'))
        self.assertEqual(response.status_code, 200)

    def test_get_update_reservation(self):
        """
        Test GET request to create reservation form.
        """

        reservation = Reservation.objects.create(
            reservee=self.user,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        response = self.client.get(
            reverse(
                'room_reservation:update_reservation', kwargs={'pk': reservation.pk}
            ))

        self.assertEqual(response.status_code, 200)

    def test_post_delete_reservation(self):
        """
        Test POST request to create reservation form.
        """

        reservation = Reservation.objects.create(
            reservee=self.user,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        response = self.client.post(
            reverse(
                'room_reservation:delete_reservation',
                kwargs={'pk': reservation.pk}
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

        is_removed = not Reservation.objects.filter(pk=reservation.pk).exists()
        self.assertTrue(is_removed, msg='reservation is removed')
