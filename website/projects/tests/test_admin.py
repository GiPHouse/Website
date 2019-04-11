from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.utils import timezone

from projects.models import Project
from registrations.models import GiphouseProfile, RoleChoice
from courses.models import Semester, SeasonChoice

User: DjangoUser = get_user_model()


class GetProjectsTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password)

        cls.semester = Semester.objects.create(
            year=2018,
            season=SeasonChoice.spring.name,
            registration_start=timezone.now(),
            registration_end=timezone.now(),
        )

        manager = User.objects.create(username='manager')
        GiphouseProfile.objects.create(
            user=manager,
            github_id='0',
            github_username='manager',
            role=RoleChoice.sdm.name
        )

        cls.project = Project.objects.create(name='test')

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_form(self):
        response = self.client.get(reverse('admin:projects_project_change', args=(self.project.id,)))
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        response = self.client.get(reverse('admin:projects_project_add'))
        self.assertEqual(response.status_code, 200)

    def test_form_save(self):
        response = self.client.post(
            reverse('admin:projects_project_add'),
            {
                'name': 'Test project',
                'semester': self.semester.id,
                'description': 'Test project description'
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Project.objects.get(semester=self.semester))
