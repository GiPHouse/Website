from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from courses.models import Course, Lecture, Semester
from lecture_registrations.models import LectureRegistration


class ModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
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
        self.assertFalse(self.lecture.registration_required)

    def test_lecture_registration_required(self):
        self.lecture.register_until = timezone.datetime(2018, 9, 10)
        self.lecture.save()
        self.assertTrue(self.lecture.registration_required)

    @freeze_time("2018-09-09")
    def test_lecture_can_register(self):
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
        self.assertFalse(self.lecture.capacity_reached)

        self.lecture.capacity = 2
        self.lecture.save()

        self.assertFalse(self.lecture.capacity_reached)

        LectureRegistration.objects.create(lecture=self.lecture)
        self.assertFalse(self.lecture.capacity_reached)
        LectureRegistration.objects.create(lecture=self.lecture)
        self.assertTrue(self.lecture.capacity_reached)
