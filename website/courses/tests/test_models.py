from django.test import TestCase
from django.utils import timezone
from courses.models import Semester, SeasonChoice, Lecture, get_slides_filename


class ModelTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.season = SeasonChoice.spring.name
        cls.year = 2019
        cls.course = Lecture.COURSE_CHOICES[0][1]
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
        """
        Test get_slides_filename function.
        """

        self.assertEqual(
            get_slides_filename(self.lecture, None),
            f'courses/slides/{self.course}-{self.title}-{self.date.strftime("%d-%b-%Y")}.pdf'

        )

    def test_lecture_string(self):
        """
        Test __str__ method of Lecture.
        """

        self.assertEqual(
            str(self.lecture),
            f'{self.course} ({self.date})',
        )
