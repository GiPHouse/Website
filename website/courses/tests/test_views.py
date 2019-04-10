from django.test import TestCase, Client
from django.utils import timezone

from courses.models import Semester, SeasonChoice, Course


class GetCoursesTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.course = Course.objects.create(name="Test Course")
        cls.season = SeasonChoice.spring.name
        cls.year = 2019

        cls.semester = Semester.objects.create(
            year=cls.year,
            season=cls.season,
            registration_start=timezone.now(),
            registration_end=timezone.now(),
        )

    def setUp(self):
        self.client = Client()

    def test_get_success(self):
        """
        Test get request of courses page.
        """

        response = self.client.get(f'/lectures/{self.year}/{self.season}/')

        self.assertEqual(response.status_code, 200)
