from django.shortcuts import reverse
from django.test import Client, TestCase

from courses.models import Semester


class GetProjectsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.semester = Semester.objects.get_or_create_current_semester()

    def setUp(self):
        self.client = Client()

    def test_get_success(self):
        response = self.client.get(
            reverse(
                "projects:projects",
                kwargs={"year": self.semester.year, "season_slug": self.semester.get_season_display()},
            )
        )

        self.assertEqual(response.status_code, 200)
