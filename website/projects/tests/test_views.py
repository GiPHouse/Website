from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester


class GetProjectsTest(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.season = Semester.SPRING
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
        response = self.client.get(reverse('projects:projects', kwargs={'year': self.year, 'season': self.season}))

        self.assertEqual(response.status_code, 200)
