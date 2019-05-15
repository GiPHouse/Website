from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase

from courses.models import Semester

from projects.models import Project

from registrations.models import GiphouseProfile, Registration, RoleChoice

User: DjangoUser = get_user_model()


class RegistrationAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password
        )

        semester = Semester.objects.create(
            year=2019,
            season=Semester.SPRING,
        )
        project = Project.objects.create(
            name="GiPHouse",
            description="Test",
            semester=semester,
        )
        cls.manager = User.objects.create(username='manager')
        GiphouseProfile.objects.create(
            user=cls.manager,
            github_id='0',
            github_username='manager',
            role=RoleChoice.sdm.name
        )
        Registration.objects.create(
            user=cls.manager,
            semester=semester,
            preference1=project,
        )

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_form(self):
        response = self.client.get(
            reverse('admin:auth_user_changelist'),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_place_in_first_project_preference(self):
        response = self.client.post(
            reverse('admin:auth_user_changelist'),
            {
                ACTION_CHECKBOX_NAME: [self.manager.pk],
                'action': 'place_in_first_project_preference',
                'index': 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
