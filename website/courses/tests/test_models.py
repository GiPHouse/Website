from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from freezegun import freeze_time

from courses.models import Course, Lecture, Semester, current_year, get_slides_filename, max_value_current_year


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.season = Semester.SPRING
        cls.year = 2019
        cls.course = Course.objects.create(name="Test Course")
        cls.date = timezone.datetime(1970, 1, 1).date()
        cls.title = 'test title'

        cls.semester = Semester.objects.create(
            year=cls.year,
            season=cls.season,
            registration_start=timezone.now(),
            registration_end=timezone.now(),
        )

        cls.lecture = Lecture.objects.create(
            semester=cls.semester,
            date=cls.date,
            course=cls.course,
            title=cls.title,
        )

    def test_get_slides_filename(self):
        """Test get_slides_filename function."""

        self.assertEqual(
            get_slides_filename(self.lecture, None),
            f'courses/slides/{self.course}-{self.title}-{self.date.strftime("%d-%b-%Y")}.pdf'

        )

    def test_lecture_string(self):
        """Test __str__ method of Lecture."""

        self.assertEqual(
            str(self.lecture),
            f'{self.course} ({self.date})',
        )

    @freeze_time("2018-01-01")
    def test_current_year(self):
        self.assertEqual(current_year(), 2018)

    @freeze_time("2018-01-01")
    def test_max_value_current_year(self):
        self.assertIsNone(max_value_current_year(2018))

    @freeze_time("2018-01-01")
    def test_max_value_current_year_raise(self):
        self.assertRaises(ValidationError, max_value_current_year, 2020)

    @freeze_time("2018-03-03")
    def test_current_semester(self):
        startreg = timezone.now().replace(year=2018, month=3, day=3, hour=0, minute=0, second=0, microsecond=1)
        endreg = timezone.now().replace(year=2018, month=6, day=6, hour=0, minute=0, second=0, microsecond=1)
        testsem = Semester.objects.create(year=2018, season=Semester.SPRING, registration_start=startreg,
                                          registration_end=endreg)
        self.assertEqual(testsem, Semester.objects.get_current_semester())

    @freeze_time("2018-09-09")
    def test_current_semester2(self):
        startreg = timezone.now().replace(year=2018, month=9, day=9, hour=0, minute=0, second=0, microsecond=1)
        endreg = timezone.now().replace(year=2018, month=10, day=6, hour=0, minute=0, second=0, microsecond=1)
        testsem = Semester.objects.create(year=2018, season=Semester.FALL, registration_start=startreg,
                                          registration_end=endreg)
        self.assertEqual(testsem, Semester.objects.get_current_semester())
