from datetime import datetime

from django.test import TestCase, Client
from django.urls import reverse
from django.utils.timezone import get_current_timezone
from django.contrib.auth import get_user_model

from room_reservation.models import Room, Reservation

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

    def test_get_calendar(self):
        """
        Test GET request to the week calendar.
        """
        response = self.client.get(reverse('room_reservation:calendar'))
        self.assertEqual(response.status_code, 200)

    def test_get_calendar_week(self):
        """
        Test GET request with a specified week.
        """
        week = 14
        response = self.client.get("{}?week={}".format(reverse('room_reservation:calendar'), week))

    def test_get_create_reservation(self):
        """
        Test GET request to create reservation form.
        """
        response = self.client.get(
            reverse('room_reservation:create_reservation'))
        self.assertEqual(response.status_code, 200)

    def test_post_create_reservation(self):
        """
        Test POST request to create reservation form.
        """
        current = Reservation.objects.all().count()
        response = self.client.post(
            reverse('room_reservation:create_reservation'),
            {
                'room': self.room.pk,
                'start_time': "04/17/2019 18:00",
                'end_time': "04/17/2019 19:00",
                'pk': '-1',
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        new = Reservation.objects.all().count()

        self.assertTrue(new > current)

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

    def test_get_update_reservation_permission_denied(self):
        """
        Test GET request to update a room reservation made by another user.
        """

        anotherone = User.objects.create_user(
            username='someone else',
            password='123',
        )

        reservation = Reservation.objects.create(
            reservee=anotherone,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        response = self.client.get(
            reverse(
                'room_reservation:update_reservation',
                kwargs={'pk': reservation.pk}
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)

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

    def test_get_delete_reservation_permission_denied(self):
        """
        Test POST request to alter someone else's reservation.
        """
        someone_else = User.objects.create_user(
            username='someone else',
            password='123',
        )

        reservation = Reservation.objects.create(
            reservee=someone_else,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        response = self.client.get(
            reverse(
                'room_reservation:update_reservation', kwargs={'pk': reservation.pk}
            ))

        self.assertEqual(response.status_code, 403)

    def test_remove_reservation_permission_denied(self):
        someone_else = User.objects.create_user(
            username='someone else',
            password='123',
        )

        reservation = Reservation.objects.create(
            reservee=someone_else,
            room=self.room,
            start_time=datetime(2005, 7, 14, 12, 00, tzinfo=self.tz),
            end_time=datetime(2005, 7, 14, 13, 00, tzinfo=self.tz),
        )

        response = self.client.get(
            reverse(
                'room_reservation:delete_reservation', kwargs={'pk': reservation.pk}
            ))

        self.assertEqual(response.status_code, 403)
                'room_reservation:delete_reservation',
                kwargs={'pk': reservation.pk}
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)

        is_removed = not Reservation.objects.filter(pk=reservation.pk).exists()
        self.assertFalse(is_removed, msg='reservation is removed')
