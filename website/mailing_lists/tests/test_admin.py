from unittest.mock import MagicMock, patch

from django.contrib.admin import AdminSite
from django.contrib.auth import get_user_model
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from courses.models import Semester

from mailing_lists.admin import CourseSemesterLinkInline, MailingListAdmin
from mailing_lists.forms import MailingListAdminForm
from mailing_lists.models import MailingList

from projects.models import Project

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

        cls.mailinglist = MailingList.objects.create(address="testmail", description="foo")
        cls.user = User.objects.create(github_id=2, github_username="BobJones")

        cls.semester = Semester.objects.create(year=2020, season=Semester.SPRING)

        cls.project = Project.objects.create(name="test", semester=cls.semester)

    def setUp(self):
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("admin:mailing_lists_mailinglist_changelist"))
        self.request.user = self.admin
        self.client = Client()
        self.client.force_login(self.admin)

    @patch("mailing_lists.admin.GSuiteSyncService")
    def test_synchronize_all_mailing_lists_calls_ok(self, gsuite_sync_service):
        sync = MagicMock()
        sync.sync_mailing_lists_as_task = MagicMock(return_value=0)
        gsuite_sync_service.return_value = sync
        mailing_list_admin = MailingListAdmin(MailingList, AdminSite)
        mailing_list_admin.synchronize_all_mailing_lists(self.request)
        sync.sync_mailing_lists_as_task.assert_called_once()

    @patch("mailing_lists.admin.GSuiteSyncService")
    def test_synchronize_selected_mailing_lists_calls_ok(self, gsuite_sync_service):
        mock_instance = MagicMock()
        gsuite_sync_service.return_value = mock_instance
        mailing_list_admin = MailingListAdmin(MailingList, AdminSite)
        mailing_list_admin.synchronize_selected_mailing_lists(
            self.request, [MailingList.objects.create(address="test")]
        )
        mock_instance.sync_mailing_lists.assert_called_once()

    def test_get_form(self):
        response = self.client.get(reverse("admin:mailing_lists_mailinglist_change", args=(self.mailinglist.id,)))
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        response = self.client.get(reverse("admin:mailing_lists_mailinglist_add"))
        self.assertEqual(response.status_code, 200)

    def test_form_new(self):
        response = self.client.post(
            reverse("admin:mailing_lists_mailinglist_add"),
            {
                "address": "abc",
                "description": "Test project description",
                "projects": self.project,
                "users": [self.user],
                "archive_instead_of_delete": False,
                "mailinglistcoursesemesterlink_set-TOTAL_FORMS": 1,
                "mailinglistcoursesemesterlink_set-INITIAL_FORMS": 0,
                "mailinglistcoursesemesterlink_set-MIN_NUM_FORMS": 0,
                "mailinglistcoursesemesterlink_set-MAX_NUM_FORMS": 1000,
                "extraemailaddress_set-TOTAL_FORMS": 1,
                "extraemailaddress_set-INITIAL_FORMS": 0,
                "extraemailaddress_set-MIN_NUM_FORMS": 0,
                "extraemailaddress_set-MAX_NUM_FORMS": 1000,
                "mailinglistalias_set-TOTAL_FORMS": 1,
                "mailinglistalias_set-INITIAL_FORMS": 0,
                "mailinglistalias_set-MIN_NUM_FORMS": 0,
                "mailinglistalias_set-MAX_NUM_FORMS": 1000,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_save(self):
        admin = MailingListAdminForm(instance=self.mailinglist, data={"address": "abc"})
        admin.save()
        self.assertIsNotNone(MailingList.objects.get(address="abc"))
