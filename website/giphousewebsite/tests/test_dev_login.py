from django.contrib.auth import get_user_model, get_user
from django.test import TestCase, override_settings
from django.urls import reverse


class TestLoginAsAnyoneDuringDevelopment(TestCase):
    def setUp(self):
        self.jeanne = get_user_model().objects.create_user(
            github_id=37,
            github_username="jeannedarc",
            first_name="Jeanne",
            last_name="de Arc",
        )
        self.alan = get_user_model().objects.create_user(
            github_id=42,
            github_username="turing",
            first_name="Alan",
            last_name="Turing",
        )
        self.user = get_user_model().objects.create_user(
            github_id=5,
            github_username="giphouse",
            first_name="Super",
            last_name="User",
        )

    def test_page_not_available_outside_DEBUG(self):
        response = self.client.get(reverse("dev-login"))
        self.assertEqual(response.status_code, 404)

    def test_page_no_posting_outside_DEBUG(self):
        response = self.client.post(
            reverse("dev-login-as", args=[self.jeanne.pk])
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(get_user(self.client).is_authenticated)

    @override_settings(DEBUG=True)
    def test_page_available_on_DEBUG(self):
        response = self.client.get(reverse("dev-login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Log in as")

    @override_settings(DEBUG=True)
    def test_successful_redirect(self):
        response = self.client.post(
            reverse("dev-login-as", args=[self.jeanne.pk])
        )
        self.assertRedirects(response, reverse("home"))
        self.assertEqual(get_user(self.client), self.jeanne)
        self.assertTrue(get_user(self.client).is_authenticated)

    @override_settings(DEBUG=True)
    def test_cannot_get_login_as_page(self):
        response = self.client.get(
            reverse("dev-login-as", args=[self.jeanne.pk])
        )
        self.assertEqual(response.status_code, 405)
        self.assertFalse(get_user(self.client).is_authenticated)

    @override_settings(DEBUG=True)
    def test_search_works_as_expected(self):
        response = self.client.get(reverse("dev-login"), {"q": "jeanne"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Jeanne de Arc")
        self.assertNotContains(response, "Alan Turing")

    def test_menu_item_not_visible_in_production(self):
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, reverse("dev-login"))

    @override_settings(DEBUG=True)
    def test_menu_item_visible_in_development(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, reverse("dev-login"))

    @override_settings(DEBUG=True)
    def test_no_login_from_remote_address(self):
        self.client.post(
            reverse("dev-login-as", args=[self.jeanne.pk]),
            REMOTE_ADDR="10.0.0.5",
        )
        self.assertFalse(get_user(self.client).is_authenticated)

    @override_settings(DEBUG=True)
    def test_login_from_ipv6_localhost(self):
        self.client.post(
            reverse("dev-login-as", args=[self.jeanne.pk]), REMOTE_ADDR="::1"
        )
        self.assertEqual(get_user(self.client), self.jeanne)
