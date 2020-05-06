from unittest.mock import MagicMock, patch

from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase

from courses.models import Course, Semester

from mailing_lists.models import MailingList

from projects.admin import ProjectAdmin
from projects.forms import ProjectAdminForm
from projects.models import Project, Repository

from registrations.models import Employee, Registration

from tasks.models import Task

User: Employee = get_user_model()


class GetProjectsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(github_id=0, github_username="admin")

        cls.semester = Semester.objects.create(year=2020, season=Semester.SPRING)
        cls.semester_archived = Semester.objects.create(year=2020, season=Semester.FALL, is_archived=True)

        cls.project = Project.objects.create(name="test", semester=cls.semester)
        cls.project_archived = Project.objects.create(name="test-archived", semester=cls.semester_archived)

        cls.manager = User.objects.create(github_id=1, github_username="manager")
        cls.repo = Repository.objects.create(name="testrepo", project=cls.project)
        cls.repo_archived = Repository.objects.create(name="testrepo-archived", project=cls.project_archived)

        cls.mailing_list = MailingList.objects.create(address="test", description=cls.project.description)

        cls.task = Task.objects.create(
            total=1,
            completed=0,
            fail=False,
            success_message="success",
            redirect_url=reverse("admin:projects_project_changelist"),
        )

        Registration.objects.create(
            user=cls.manager,
            semester=cls.semester,
            project=cls.project,
            course=Course.objects.sdm(),
            preference1=cls.project,
            experience=Registration.EXPERIENCE_ADVANCED,
        )

    def setUp(self):
        site = AdminSite
        self.project_admin = ProjectAdmin(Project, site)
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("admin:projects_project_changelist"))
        self.request.user = self.admin
        self.client = Client()
        self.client.force_login(self.admin)
        self.old_error = messages.error
        self.old_warning = messages.warning
        self.old_success = messages.success
        self.sync_mock = MagicMock()
        self.sync_mock.perform_sync = MagicMock()
        self.sync_mock.teams_created = 1
        self.sync_mock.repos_created = 1
        self.sync_mock.users_invited = 1
        self.sync_mock.users_removed = 1
        self.sync_mock.repos_archived = 1
        self.github_mock = MagicMock(return_value=self.sync_mock)
        messages.error = MagicMock()
        messages.warning = MagicMock()
        messages.success = MagicMock()

    def tearDown(self):
        messages.error = self.old_error
        messages.warning = self.old_warning
        messages.success = self.old_success

    def test_get_form(self):
        response = self.client.get(reverse("admin:projects_project_change", args=(self.project.id,)))
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        response = self.client.get(reverse("admin:projects_project_add"))
        self.assertEqual(response.status_code, 200)

    def test_form_save_new(self):
        response = self.client.post(
            reverse("admin:projects_project_add"),
            {
                "name": "Test project",
                "semester": self.semester.id,
                "email": "a@a.com",
                "description": "Test project description",
                "managers": self.manager.id,
                "repository_set-TOTAL_FORMS": 1,
                "repository_set-INITIAL_FORMS": 0,
                "repository_set-MIN_NUM_FORMS": 0,
                "repository_set-MAX_NUM_FORMS": 1,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(Project.objects.get(name="Test project"))

    def test_create_mail_is_valid(self):
        p1 = Project(name="p1", semester=Semester(year=2020, season="Spring"), description="test1")
        p2 = Project(name="p23352135no/fe", semester=Semester(year=2030, season="Spring"), description="test2")

        self.client.post(
            reverse("admin:projects_project_changelist"),
            {ACTION_CHECKBOX_NAME: [self.project.pk], "action": "create_mailing_lists", "index": 0},
        )

        self.assertNotEqual(MailingList.objects.filter(projects=p1), [])
        self.assertNotEqual(MailingList.objects.filter(projects=p2), [])

    def test_create_mailing_lists(self):
        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {ACTION_CHECKBOX_NAME: [self.project.pk], "action": "create_mailing_lists", "index": 0},
        )

        self.assertEqual(response.status_code, 302)

    def test_projectteam_added_in_mailing_list(self):
        pa = ProjectAdmin(ProjectAdminForm, admin_site=None)

        sem1 = Semester.objects.create(year=2024, season=1)
        sem2 = Semester.objects.create(year=2019, season=0)
        course = Course.objects.create(name="testcourse")

        test_project = Project.objects.create(name="test_project", semester=sem1, description="1")
        test_project2 = Project.objects.create(name="test_project2", semester=sem2, description="2")
        test_user1 = User.objects.create(github_id=123, github_username="Bob")
        test_user2 = User.objects.create(github_id=1234, github_username="Nick")
        test_user3 = User.objects.create(github_id=1235, github_username="James")

        Registration.objects.create(
            user=test_user1,
            semester=sem1,
            project=test_project,
            course=course,
            preference1=test_project,
            experience=1,
            education_background="nothing",
        )
        Registration.objects.create(
            user=test_user2,
            semester=sem2,
            project=test_project,
            course=course,
            preference1=test_project,
            experience=1,
            education_background="nothing",
        )
        Registration.objects.create(
            user=test_user3,
            semester=sem1,
            project=test_project,
            course=course,
            preference1=test_project,
            experience=1,
            education_background="nothing",
        )

        pa.create_mailing_lists(self.request, [test_project, test_project2])

        messages.success.assert_called()

        lists = MailingList.objects.all()
        user_list = []

        for mailing_list in lists:
            reg = Registration.objects.all()
            for r in reg:
                if mailing_list.address == r.project.generate_email():
                    user_list.append(r.user.github_id)

        self.assertIn(test_user1.github_id, user_list)
        self.assertIn(test_user2.github_id, user_list)
        self.assertIn(test_user3.github_id, user_list)

    def test_non_duplicate_project_in_mailing_list(self):
        pa = ProjectAdmin(ProjectAdminForm, admin_site=None)
        sem1 = Semester.objects.create(year=2024, season=1)
        test_project = Project.objects.create(name="test_project", semester=sem1, description="1")

        pa.create_mailing_lists(self.request, [test_project])
        pa.create_mailing_lists(self.request, [test_project])

        messages.error.assert_called()

    def test_synchronise_projects_to_GitHub(self):
        all_projects = Project.objects.all()
        self.sync_mock.perform_asynchronous_sync.return_value = self.task.id
        with patch("projects.admin.GitHubSync", self.github_mock):
            self.project_admin.synchronise_to_GitHub(self.request, all_projects)
        self.github_mock.assert_called_once()
        self.assertEqual(list(self.github_mock.call_args.args[0]), list(Project.objects.all()))
        self.sync_mock.perform_asynchronous_sync.assert_called_once()

    def test_synchronise_all_projects_to_GitHub(self):
        original_sync_action = self.project_admin.synchronise_to_GitHub
        self.project_admin.synchronise_to_GitHub = MagicMock()
        self.project_admin.synchronise_all_projects_to_GitHub(self.request)
        self.project_admin.synchronise_to_GitHub.assert_called_once()
        self.project_admin.synchronise_to_GitHub = original_sync_action
