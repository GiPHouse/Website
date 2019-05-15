from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester

from projects.models import Project

from registrations.models import GiphouseProfile, Role

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
            season=Semester.SPRING,
            registration_start=timezone.now(),
            registration_end=timezone.now(),
        )

        sdm, created = Role.objects.get_or_create(name='SDM Student')

        manager = User.objects.create(username='manager')
        GiphouseProfile.objects.create(
            user=manager,
            github_id='0',
            github_username='manager',
        )
        manager.groups.add(sdm) if (sdm) else manager.groups.add(created)

        cls.project = Project.objects.create(name='test', semester=cls.semester)

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
        self.assertIsNotNone(Project.objects.get(name='Test project'))
