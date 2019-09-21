from django.test import Client, TestCase
from django.urls import reverse

from giphousewebsite.mixins import LoginRequiredMessageMixin


class LoginRequiredMessageMixinTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_handle_no_permission(self):
        response = self.client.get(reverse("questionnaires:overview"), follow=True)

        mixin = LoginRequiredMessageMixin()
        self.assertRedirects(response, f"{mixin.get_login_url()}?next={reverse('questionnaires:overview')}")
        self.assertEquals(list(map(str, response.context["messages"])), [mixin.message])
