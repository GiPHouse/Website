from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase

from registrations.models import GiphouseProfile

User: DjangoUser = get_user_model()


class RegistrationAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = 'hunter2'
        cls.admin = User.objects.create_superuser(
            username='admin',
            email='',
            password=cls.admin_password)

        manager = User.objects.create(username='manager')
        GiphouseProfile.objects.create(
            user=manager,
            github_id='0',
            github_username='manager',
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
