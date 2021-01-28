import json

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from registrations.models import Employee

from room_reservation.models import Reservation, Room

User: Employee = get_user_model()


class ReservationTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(github_id=0, github_username="test")
        cls.other_user = User.objects.create_user(github_id=1, github_username="test2")

        cls.room = Room.objects.create(name="New York", location="Merc 0.1337")

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
        self.client.force_login(self.user)

    def test_get_calendar(self):
        response = self.client.get(reverse("room_reservation:calendar"))
        self.assertEqual(response.status_code, 200)

    def test_add_reservation(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertIsNotNone(Reservation.objects.filter(pk=json.loads(response.content)["pk"]).first())

    def test_reservation_too_long(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 5, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Reservation too long. Please shorten your reservation")

    def test_end_before_start(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Start time needs to be before end time")

    def test_outside_office_hours(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 6, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 7, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Please enter times between 8:00 and 18:00")

    def test_start_outside_office_hours(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 3, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 13, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Please enter times between 8:00 and 18:00")

    def test_end_outside_office_hours(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 13, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 20, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Please enter times between 8:00 and 18:00")

    def test_in_weekend(self):
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 3, 13, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 3, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Rooms cannot be reserved in the weekends")

    def test_double_reservation(self):
        self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        response = self.client.post(
            reverse("room_reservation:create_reservation"),
            {
                "room": self.room.pk,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Room already reserved in this timeslot")

    def test_bad_request(self):
        response = self.client.post(reverse("room_reservation:create_reservation"), {"test": "hai"})
        self.assertEqual(response.status_code, 400)

    def test_update_reservation(self):
        response = self.client.post(
            reverse("room_reservation:update_reservation", kwargs={"pk": self.user_reservation.pk}),
            {
                "room": self.user_reservation.room_id,
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, '"ok": true')

    def test_update_reservation_malformed(self):
        response = self.client.post(
            reverse("room_reservation:update_reservation", kwargs={"pk": self.user_reservation.pk}),
            {
                "start_time": timezone.datetime(2019, 3, 4, 14, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_update_reservation_outside_hours(self):
        response = self.client.post(
            reverse("room_reservation:update_reservation", kwargs={"pk": self.user_reservation.pk}),
            {
                "room": self.user_reservation.room_id,
                "start_time": timezone.datetime(2019, 3, 4, 5, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "Please enter times between 8:00 and 18:00")

    def test_update_nonexisting(self):
        response = self.client.post(
            reverse("room_reservation:update_reservation", kwargs={"pk": 100}),
            {
                "room": self.user_reservation.room_id,
                "start_time": timezone.datetime(2019, 3, 4, 8, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "This reservation does not exist")

    def test_update_other_user(self):
        response = self.client.post(
            reverse("room_reservation:update_reservation", kwargs={"pk": self.other_reservation.pk}),
            {
                "room": self.user_reservation.room_id,
                "start_time": timezone.datetime(2019, 3, 4, 8, 0, 0, tzinfo=timezone.get_current_timezone()),
                "end_time": timezone.datetime(2019, 3, 4, 16, 0, 0, tzinfo=timezone.get_current_timezone()),
            },
            content_type="application/json",
        )
        self.assertContains(response, "You can only update your own events")

    def test_delete_reservation(self):
        response = self.client.post(
            reverse("room_reservation:delete_reservation", kwargs={"pk": self.user_reservation.pk})
        )
        self.assertContains(response, '"ok": true')

    def test_delete_nonexisting(self):
        response = self.client.post(reverse("room_reservation:delete_reservation", kwargs={"pk": 100}))
        self.assertContains(response, "This reservation does not exist")

    def test_delete_other_user(self):
        response = self.client.post(
            reverse("room_reservation:delete_reservation", kwargs={"pk": self.other_reservation.pk})
        )
        self.assertContains(response, "You can only delete your own events")
