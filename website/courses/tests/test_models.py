from freezegun import freeze_time

from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError

from courses.models import Semester
from courses.models import SeasonChoice
from courses.models import Lecture
from courses.models import get_slides_filename
from courses.models import Course
from courses.models import current_year
from courses.models import max_value_current_year


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.season = SeasonChoice.spring.name
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
