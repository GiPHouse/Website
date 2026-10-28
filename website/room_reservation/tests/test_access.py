from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from room_reservation.models import Reservation, Room
from courses.models import Course, Semester
from projects.models import Project
from registrations.models import Registration


class CalendarAccessTest(TestCase):
    def _create_user(self, gid, first, last):
        return get_user_model().objects.create_user(
            github_id=gid,
            github_username=first + last,
            first_name=first.capitalize(),
            last_name=last.capitalize(),
        )

    def setUp(self):
        self.defaultUser = self._create_user(0, "jane", "austen")

    def test_anonymous_visitor_is_redirected(self):
        response = self.client.get(reverse("room_reservation:calendar"))
        self.assertRedirects(response, "/?next=/reservations/")

    def test_logged_in_user_gets_calendar(self):
        self.client.force_login(self.defaultUser)
        response = self.client.get(reverse("room_reservation:calendar"))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_visitor_does_not_have_calendar_menu_item(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, "Room Reservations")

    def test_logged_in_user_does_have_calendar_menu_item(self):
        self.client.force_login(self.defaultUser)
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Room Reservations")

    def _create_room(self, name):
        return Room.objects.create(name=name, location="The Moon")

    def _create_reservation(self, user, room):
        return Reservation.objects.create(
            reservee=user,
            room=room,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(days=1),
        )

    def test_current_reservation_shows_up_for_inactive_student(self):
        owner = self._create_user(12, "emily", "bronte")
        room = self._create_room("Amsterdam")
        self._create_reservation(owner, room)
        self.client.force_login(self.defaultUser)
        response = self.client.get(reverse("room_reservation:calendar"))
        self.assertContains(response, "Amsterdam (Emily)")

    def test_current_registration_shows_up_for_student_in_project(self):
        agatha = self._create_user(42, "agatha", "christie")
        semester = Semester.objects.get_or_create_current_semester()
        project = Project.objects.create(
            name="Test Project", semester=semester, slug="test-project"
        )
        registration = Registration.objects.create(
            user=agatha,
            course=Course.objects.se(),
            semester=semester,
            dev_experience=1,
        )
        registration.projects.add(project)
        room = self._create_room("Miami")
        self._create_reservation(agatha, room)
        self.client.force_login(self.defaultUser)
        response = self.client.get(reverse("room_reservation:calendar"))
        self.assertContains(response, "Miami Test Project")
        self.assertNotContains(response, "Miami(Agatha)")

