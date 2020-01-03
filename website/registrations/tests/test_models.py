from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Semester

from projects.models import Project

from registrations.models import Employee

User: Employee = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.first_name = "Test"
        cls.last_name = "Test"
        cls.project_name = "testproject"

        cls.test_user = User.objects.create_user(github_id=1, first_name=cls.first_name, last_name=cls.last_name)

        cls.test_semester = Semester.objects.get_or_create_current_semester()

        cls.test_project = Project.objects.create(name=cls.project_name, semester=cls.test_semester)

    def test_semester_str(self):

        self.assertEqual(
            f"{self.test_semester.get_season_display()} {self.test_semester.year}", str(self.test_semester)
        )

    def test_project_str(self):

        self.assertEqual(f"{self.project_name} ({self.test_semester})", str(self.test_project))
