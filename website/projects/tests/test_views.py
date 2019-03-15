from django.test import TestCase, Client
from django.utils import timezone
from django.shortcuts import reverse

from courses.models import Semester, SeasonChoice


class GetProjectsTest(TestCase):

    @classmethod
    def setUpTestData(cls):

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
        """Test get request of projects page."""

        response = self.client.get(reverse('projects:projects', kwargs={'year': self.year, 'season': self.season}))

        self.assertEqual(response.status_code, 200)
