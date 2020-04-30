from unittest.mock import MagicMock, patch

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

from mailing_lists.admin import CourseSemesterLinkInline, MailingListAdmin
from mailing_lists.models import MailingList

from registrations.models import Employee

User: Employee = get_user_model()


class CourseSemesterLinkInlineTest(TestCase):
    @patch("django.contrib.admin.TabularInline.formfield_for_dbfield")
    def test_formfield_for_dbfield(self, formfield_for_dbfield):
        inline = CourseSemesterLinkInline(MailingList, AdminSite())
        dbfield_mock = MagicMock()
        formfield = MagicMock()
        formfield.widget = MagicMock()
        formfield_for_dbfield.return_value = formfield

        dbfield_mock.name = "course"
        inline.formfield_for_dbfield(dbfield_mock, None)
        self.assertFalse(formfield.widget.can_add_related)
        self.assertFalse(formfield.widget.can_change_related)

        formfield.reset_mock()

        dbfield_mock.name = "semester"
        inline.formfield_for_dbfield(dbfield_mock, None)
        self.assertFalse(formfield.widget.can_add_related)
        self.assertFalse(formfield.widget.can_change_related)

        formfield.reset_mock()

        dbfield_mock.name = "mailing_list"
        inline.formfield_for_dbfield(dbfield_mock, None)


class MailingListAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(github_id=0, github_username="admin")

    def setUp(self):
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("admin:mailing_lists_mailinglist_changelist"))
        self.request.user = self.admin

    @patch("mailing_lists.admin.GSuiteSyncService")
    def test_synchronize_all_mailing_lists_calls_ok(self, gsuite_sync_service):
        mock_instance = MagicMock()
        gsuite_sync_service.return_value = mock_instance
        mailing_list_admin = MailingListAdmin(MailingList, AdminSite)
        mailing_list_admin.synchronize_all_mailing_lists(self.request)
        mock_instance.sync_mailing_lists.assert_called_once()

    @patch("mailing_lists.admin.GSuiteSyncService")
    def test_synchronize_selected_mailing_lists_calls_ok(self, gsuite_sync_service):
        mock_instance = MagicMock()
        gsuite_sync_service.return_value = mock_instance
        mailing_list_admin = MailingListAdmin(MailingList, AdminSite)
        mailing_list_admin.synchronize_selected_mailing_lists(
            self.request, [MailingList.objects.create(address="test")]
        )
        mock_instance.sync_mailing_lists.assert_called_once()
