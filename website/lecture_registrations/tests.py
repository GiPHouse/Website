from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from freezegun import freeze_time

from courses.models import Course, Lecture, Semester

from lecture_registrations.models import LectureRegistration

from projects.models import Project

from registrations.models import Employee, Registration


class ModelTest(TestCase):
    """Test the lecture registration model logic."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.season = Semester.SPRING
        cls.year = 2019
        cls.course = Course.objects.create(name="Test Course")
        cls.date = timezone.datetime(1970, 1, 1).date()
        cls.title = "test title"

        cls.semester = Semester.objects.create(
            year=cls.year, season=cls.season, registration_start=timezone.now(), registration_end=timezone.now()
        )

        cls.lecture = Lecture.objects.create(semester=cls.semester, date=cls.date, course=cls.course, title=cls.title)

    def test_lecture_registration_not_required(self):
        """Test registration not required."""
        self.assertFalse(self.lecture.registration_required)

    def test_lecture_registration_required(self):
        """Test registration is required."""
        self.lecture.register_until = timezone.datetime(2018, 9, 10)
        self.lecture.save()
        self.assertTrue(self.lecture.registration_required)

    @freeze_time("2018-09-09")
    def test_lecture_can_register(self):
        """Test when registration is possible."""
        with self.subTest("If registration is not required at all"):
            self.assertTrue(self.lecture.can_register)

        with self.subTest("If registration deadline is in the future"):
            self.lecture.register_until = timezone.now().replace(
                year=2018, month=9, day=10, hour=0, minute=0, second=0, microsecond=1
            )
            self.lecture.save()
            self.assertTrue(self.lecture.can_register)

        with self.subTest("If registration deadline is in the past"):
            self.lecture.register_until = timezone.now().replace(
                year=2018, month=9, day=8, hour=0, minute=0, second=0, microsecond=1
            )
            self.lecture.save()
            self.assertFalse(self.lecture.can_register)

    def test_lecture_capacity_reached(self):
        """Test when capacity is reached."""
        self.assertFalse(self.lecture.capacity_reached)

        self.lecture.capacity = 2
        self.lecture.save()

        self.assertFalse(self.lecture.capacity_reached)

        LectureRegistration.objects.create(lecture=self.lecture)
        self.assertFalse(self.lecture.capacity_reached)
        LectureRegistration.objects.create(lecture=self.lecture)
        self.assertTrue(self.lecture.capacity_reached)


class ViewTest(TestCase):
    """Test the lecture registration and unregistration views."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data."""
        cls.user = Employee.objects.create_user(github_id=0, github_username="test")
        cls.season = Semester.SPRING
        cls.year = 2019
        cls.other_year = 2017
        cls.course = Course.objects.create(name="Test Course")
        cls.date = timezone.datetime(1970, 1, 1).date()
        cls.title = "test title"

        cls.semester = Semester.objects.create(
            year=cls.year, season=cls.season, registration_start=timezone.now(), registration_end=timezone.now()
        )
        cls.other_semester = Semester.objects.create(
            year=cls.other_year, season=cls.season, registration_start=timezone.now(), registration_end=timezone.now()
        )

        cls.se = Course.objects.se()
        cls.experience = Registration.EXPERIENCE_BEGINNER
        cls.project_preference1 = Project.objects.create(
            semester=cls.semester, name="project1", slug="project1", description="Test Project 1"
        )

        cls.project_preference2 = Project.objects.create(
            semester=cls.semester, name="project2", slug="project2", description="Test Project 2"
        )

        cls.project_preference3 = Project.objects.create(
            semester=cls.semester, name="project3", slug="project3", description="Test Project 3"
        )
        cls.registration = Registration.objects.create(
            user=cls.user,
            experience=cls.experience,
            course_id=cls.se.id,
            preference1_id=cls.project_preference1.id,
            preference2_id=cls.project_preference2.id,
            preference3_id=cls.project_preference3.id,
            semester=cls.semester,
        )

        cls.lecture = Lecture.objects.create(
            semester=cls.semester,
            date=cls.date,
            course=cls.course,
            title=cls.title,
            capacity=2,
            register_until=timezone.now().replace(
                year=2018, month=9, day=10, hour=0, minute=0, second=0, microsecond=1
            ),
        )

    def setUp(self):
        """Set up a client."""
        self.client = Client()
        self.client.force_login(self.user)

    @freeze_time("2018-09-09")
    def test_register(self):
        """Registering for a lecture should work fine."""
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 1)
        self.assertContains(response, "You are now registered")
        response = self.client.post(
            reverse("lecture_registrations:unregister_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)
        self.assertContains(response, "You are unregistered")

    @freeze_time("2018-09-09")
    def test_register_non_existing_lecture(self):
        """Registering for a non-existing lecture should fail."""
        response = self.client.post(reverse("lecture_registrations:register_for_lecture", args=[3]), follow=True)
        self.assertEqual(response.status_code, 404)

    @freeze_time("2018-09-09")
    def test_unregister_non_existing_lecture(self):
        """Unregistering for a non-existing lecture should fail."""
        response = self.client.post(reverse("lecture_registrations:unregister_for_lecture", args=[3]), follow=True)
        self.assertEqual(response.status_code, 404)

    @freeze_time("2018-09-09")
    def test_register_wrong_semester(self):
        """Registering a user that is not registered for that semester should fail."""
        self.registration.semester = self.other_semester
        self.registration.save()
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "You are not registered for this semester")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)

    @freeze_time("2018-09-09")
    def test_register_already_registered(self):
        """Registering a user when they are already registered should fail."""
        LectureRegistration.objects.create(lecture=self.lecture, employee=self.user)
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "You were already registered")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 1)

    @freeze_time("2018-09-09")
    def test_register_no_registration_required(self):
        """Registering a user when no registration is required should fail."""
        self.lecture.register_until = None
        self.lecture.save()
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "No registration required")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)

    @freeze_time("2018-09-13")
    def test_register_registration_closed(self):
        """Registering a user when the deadline has passed should fail."""
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "Registration is closed")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)

    @freeze_time("2018-09-13")
    def test_unregister_registration_closed(self):
        """Unregistering a user when the deadline has passed should fail."""
        LectureRegistration.objects.create(lecture=self.lecture, employee=self.user)
        response = self.client.post(
            reverse("lecture_registrations:unregister_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "Registration is closed")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 1)

    @freeze_time("2018-09-09")
    def test_register_capacity_reached(self):
        """Registering a user when the lecture's capacity has been reached should fail."""
        LectureRegistration.objects.create(lecture=self.lecture, employee=None)
        LectureRegistration.objects.create(lecture=self.lecture, employee=None)
        response = self.client.post(
            reverse("lecture_registrations:register_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "Capacity has been reached")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 2)

    @freeze_time("2018-09-09")
    def test_unregister_not_registered(self):
        """Unregistering a user that is not registered should have no effect."""
        response = self.client.post(
            reverse("lecture_registrations:unregister_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "You were not registered")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)

    @freeze_time("2018-09-09")
    def test_unregister(self):
        """Unregistering a user that was registered should work fine."""
        LectureRegistration.objects.create(lecture=self.lecture, employee=self.user)
        response = self.client.post(
            reverse("lecture_registrations:unregister_for_lecture", args=[self.lecture.pk]), follow=True
        )
        self.assertContains(response, "You are unregistered")
        self.assertEqual(response.status_code, 200)
        self.lecture.refresh_from_db()
        self.assertEqual(self.lecture.lectureregistration_set.count(), 0)
