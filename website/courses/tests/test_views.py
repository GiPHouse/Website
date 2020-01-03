from django.shortcuts import reverse
from django.test import Client, TestCase

from courses.models import Course, Semester


class GetCoursesTest(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.course = Course.objects.create(name="Test Course")
        cls.spring = Semester.objects.create(year=2019, season=Semester.SPRING)

        cls.fall = Semester.objects.create(year=2019, season=Semester.FALL)

    def setUp(self):
        self.client = Client()

    def test_get_success_spring(self):
        response = self.client.get(
            reverse(
                "courses:lectures", kwargs={"year": self.spring.year, "season_slug": self.spring.get_season_display()}
            )
        )
        self.assertContains(response, self.course.name, status_code=200)

    def test_get_success_fall(self):
        response = self.client.get(
            reverse(
                "courses:lectures", kwargs={"year": self.spring.year, "season_slug": self.fall.get_season_display()}
            )
        )
        self.assertContains(response, self.course.name, status_code=200)

    def test_get_fail(self):
        response = self.client.get(f"/projects/{self.spring.year}/not-a-season/")
        self.assertEqual(response.status_code, 404)
