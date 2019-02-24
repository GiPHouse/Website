from unittest import mock

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.utils import timezone

from registrations.models import Project
from courses.models import Semester, SeasonChoice

User = get_user_model()


class RedirectTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_base_url_redirects_to_step_1(self):
        response = self.client.get('/register/')

        self.assertRedirects(response, reverse('registrations:step1'), fetch_redirect_response=False)


class Step1Test(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_user_password = 'password'

        cls.test_user = User.objects.create_user(
            username='test_user',
            password=cls.test_user_password
        )
        cls.test_user.backend = ''

        Semester.objects.create(
            year=timezone.now().year,
            semester=SeasonChoice.spring.name,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
        )

    def setUp(self):
        self.client = Client()

    def test_step1(self):
        response = self.client.get('/register/step1')

        self.assertEqual(response.status_code, 200)

    def test_step1_authenticated(self):
        self.client.login(
            username=self.test_user.username,
            password=self.test_user_password,
        )

        response = self.client.get('/register/step1')

        self.assertRedirects(response, reverse('home'))

    @mock.patch('courses.models.SemesterManager.get_current_registration')
    def test_step1_no_semester(self, mock_get_current_registration):
        mock_get_current_registration.return_value = None

        response = self.client.get('/register/step1')

        self.assertRedirects(response, reverse('home'))


class Step2Test(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.semester = Semester.objects.create(
            year=timezone.now().year,
            semester=SeasonChoice.spring.name,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
        )

        cls.first_name = 'Test'
        cls.last_name = 'Test'
        cls.email = 'test@test.com'
        cls.github_username = 'test'
        cls.github_id = 1
        cls.student_number = 's4593847'

        cls.project_preference1 = Project.objects.create(
            semester=cls.semester,
            name='project1',
            description='Test Project 1',
        )

        cls.project_preference2 = Project.objects.create(
            semester=cls.semester,
            name='project2',
            description='Test Project 2',
        )

        cls.project_preference3 = Project.objects.create(
            semester=cls.semester,
            name='project3',
            description='Test Project 3',
        )

    def setUp(self):
        self.client = Client()

        self.session = self.client.session
        self.session['github_id'] = self.github_id
        self.session['github_username'] = self.github_username
        self.session['github_email'] = self.email
        self.session['github_name'] = f'{self.first_name} {self.last_name}'

        self.session.save()

    def test_step2(self):
        response = self.client.get('/register/step2')
        self.assertEqual(response.status_code, 200)

    def test_step2_no_github_id(self):
        del self.session['github_id']
        self.session.save()

        response = self.client.get('/register/step2')

        self.assertEqual(response.status_code, 400)
