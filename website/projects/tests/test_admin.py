from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Course, Semester, current_season

from projects.models import Project

from registrations.models import GiphouseProfile, Registration

User: DjangoUser = get_user_model()


class GetProjectsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(username="admin", email="", password=cls.admin_password)

        cls.semester = Semester.objects.create(
            year=timezone.now().year,
            season=current_season(),
            registration_start=timezone.now(),
            registration_end=timezone.now(),
        )

        cls.project = Project.objects.create(name="test", semester=cls.semester)
        cls.manager = User.objects.create(username="manager")
        GiphouseProfile.objects.create(user=cls.manager, github_id="0", github_username="manager")
        Registration.objects.create(
            user=cls.manager,
            semester=cls.semester,
            project=cls.project,
            course=Course.objects.sdm(),
            preference1=cls.project,
            experience=Registration.EXPERIENCE_ADVANCED,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_form(self):
        response = self.client.get(reverse("admin:projects_project_change", args=(self.project.id,)))
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        response = self.client.get(reverse("admin:projects_project_add"))
        self.assertEqual(response.status_code, 200)

    def test_form_save_new(self):
        response = self.client.post(
            reverse("admin:projects_project_add"),
            {
                "name": "Test project",
                "semester": self.semester.id,
                "email": "a@a.com",
                "description": "Test project description",
                "managers": self.manager.id,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Project.objects.get(name="Test project"))

    def test_csv_export(self):
        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {ACTION_CHECKBOX_NAME: [self.project.pk], "action": "export_addresses_csv", "index": 0},
        )
        self.assertEqual(response.status_code, 200)
