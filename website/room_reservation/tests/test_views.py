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

    def test_get_calendar_week(self):
        response = self.client.get("{}?week={}".format(reverse('room_reservation:calendar'), 14))
        self.assertEqual(response.status_code, 200)

    def test_get_create_reservation(self):
        response = self.client.get(reverse('room_reservation:create_reservation'))
        self.assertEqual(response.status_code, 200)

    def test_post_create_reservation(self):
        count_before = Reservation.objects.all().count()
        response = self.client.post(
            reverse('room_reservation:create_reservation'),
            {
                'room': self.room.pk,
                'start_time': "04/17/2019 10:00",
                'end_time': "04/17/2019 12:00",
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Reservation.objects.all().count(), count_before + 1)

    def test_get_update_reservation(self):

        response = self.client.get(
            reverse('room_reservation:update_reservation', kwargs={'pk': self.user_reservation.pk})
        )

        self.assertEqual(response.status_code, 200)

    def test_get_update_reservation_permission_denied(self):

        response = self.client.get(
            reverse(
                'room_reservation:update_reservation',
                kwargs={'pk': self.other_reservation.pk}
            ),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)

    def test_post_delete_reservation(self):
        response = self.client.post(
            reverse('room_reservation:delete_reservation', kwargs={'pk': self.user_reservation.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.filter(pk=self.user_reservation.pk).exists())

    def test_get_delete_reservation_permission_denied(self):

        response = self.client.get(
            reverse('room_reservation:update_reservation', kwargs={'pk': self.other_reservation.pk})
        )

        self.assertEqual(response.status_code, 403)

    def test_remove_reservation_permission_denied(self):

        response = self.client.get(
            reverse('room_reservation:delete_reservation', kwargs={'pk': self.other_reservation.pk}),
            follow=True,
        )

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Reservation.objects.filter(pk=self.other_reservation.pk).exists())
