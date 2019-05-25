from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester

from projects.models import Project

from registrations.models import GiphouseProfile, Registration, Role

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

        sdm, _ = Role.objects.get_or_create(name=Role.SDM)
        semester, _ = Semester.objects.get_or_create(
            year=timezone.now().year,
            season=Semester.SPRING,
            defaults={
                'registration_start': timezone.now() - timezone.timedelta(days=30),
                'registration_end': timezone.now() + timezone.timedelta(days=30),
            }
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
        )
        cls.manager.groups.add(sdm)
        cls.manager.save()

        cls.message = {
            'date_joined_0': "2000-12-01",
            'date_joined_1': "12:00:00",
            'initial-date_joined_0': "2000-12-01",
            'initial-date_joined_1': "12:00:00",
            'project': project.id,
            'role': sdm.id,
            'giphouseprofile-TOTAL_FORMS': 1,
            'giphouseprofile-INITIAL_FORMS': 0,
            'giphouseprofile-MIN_NUM_FORMS': 0,
            'giphouseprofile-MAX_NUM_FORMS': 1,
            'giphouseprofile-0-github_id': 4,
            'giphouseprofile-0-github_username': "bob",
            'giphouseprofile-0-student_number': "s0000000",
            'registration_set-TOTAL_FORMS': 1,
            'registration_set-INITIAL_FORMS': 0,
            'registration_set-MIN_NUM_FORMS': 0,
            'registration_set-MAX_NUM_FORMS': 1,
            'registration_set-0-preference1': project.id,
            'registration_set-0-semester': semester.id,
            '_save': 'Save'
        }

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
            reverse('admin:registrations_student_changelist'),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_form_save_with_role_and_project(self):
        response = self.client.post(
            reverse('admin:registrations_student_add'),
            self.message,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(giphouseprofile__student_number='s0000000'))

    def test_form_save_without_role_and_project(self):
        self.message['role'] = ''
        self.message['project'] = ''
        response = self.client.post(
            reverse('admin:registrations_student_add'),
            self.message,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(giphouseprofile__student_number='s0000000'))

    def test_place_in_first_project_preference(self):
        response = self.client.post(
            reverse('admin:registrations_student_changelist'),
            {
                ACTION_CHECKBOX_NAME: [self.manager.pk],
                'action': 'place_in_first_project_preference',
                'index': 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
