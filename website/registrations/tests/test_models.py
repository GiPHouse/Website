from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration

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

    def test_registration_is_director_correct(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            education_background="Test",
        )

        self.assertTrue(reg.is_director)

    def test_registration_is_director_with_project(self):
        reg = Registration.objects.create(
            user=self.test_user,
            project=self.test_project,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            education_background="Test",
        )

        self.assertFalse(reg.is_director)

    def test_registration_is_director_with_sde(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sde(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            education_background="Test",
        )

        self.assertFalse(reg.is_director)

    def test_registration_is_director_with_se_and_project(self):
        reg = Registration.objects.create(
            user=self.test_user,
            project=self.test_project,
            course=Course.objects.se(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            education_background="Test",
        )

        self.assertFalse(reg.is_director)

    def test_project_str(self):

        self.assertEqual(f"{self.project_name} ({self.test_semester})", str(self.test_project))
