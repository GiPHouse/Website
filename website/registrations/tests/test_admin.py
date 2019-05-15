from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester

from projects.models import Project

from registrations.models import GiphouseProfile, Role, SDM

User: DjangoUser = get_user_model()


class RegistrationAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password)

        cls.sdm, created = Role.objects.get_or_create(name=SDM)

        manager = User.objects.create(username='manager')
        GiphouseProfile.objects.create(
            user=manager,
            github_id='0',
            github_username='manager',
        )
        manager.groups.add(cls.sdm)

        cls.semester = Semester.objects.create(
            year=2019,
            season=Semester.SPRING,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=60)
        )

        cls.project, created = Project.objects.get_or_create(
            semester=cls.semester,
            name="Test Project",
            description="Description",
        )

        cls.message = {
            'id': 10,
            'date_joined_0': "2000-12-01",
            'date_joined_1': "12:00:00",
            'initial-date_joined_0': "2000-12-01",
            'initial-date_joined_1': "12:00:00",
            'project': cls.project.id,
            'role': cls.sdm.id,
            'giphouseprofile-TOTAL_FORMS': 1,
            'giphouseprofile-INITIAL_FORMS': 0,
            'giphouseprofile-MIN_NUM_FORMS': 0,
            'giphouseprofile-MAX_NUM_FORMS': 1,
            'giphouseprofile-0-github_id': 4,
            'giphouseprofile-0-github_username': "bob",
            'giphouseprofile-0-student_number': "s4451323",
            'registration_set-TOTAL_FORMS': 1,
            'registration_set-INITIAL_FORMS': 0,
            'registration_set-MIN_NUM_FORMS': 0,
            'registration_set-MAX_NUM_FORMS': 1,
            'registration_set-0-preference1': cls.project.id,
            'registration_set-0-semester': cls.semester.id,
            '_save': 'Save'
        }

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_form(self):
        response = self.client.get(
            reverse('admin:auth_user_changelist'),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_form_save_with_role_and_project(self):
        response = self.client.post(
            reverse('admin:auth_user_add'),
            self.message,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.filter(pk=4))

    def test_form_save_without_role_and_project(self):
        self.message['role'] = ''
        self.message['project'] = ''
        self.message['id'] = 5
        response = self.client.post(
            reverse('admin:auth_user_add'),
            self.message,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.filter(pk=5))
