from unittest.mock import MagicMock, patch

from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase

from freezegun import freeze_time

from github import UnknownObjectException, GithubException

from courses.models import Course, Semester

from mailing_lists.models import MailingList

from projects.admin import (
    ProjectAdmin,
    ProjectAdminArchivedFilter,
    NewRepositoryInline,
    ExistingRepositoryInline,
)
from projects.forms import ProjectAdminForm
from projects.models import (
    Project,
    Repository,
    NewRepository,
    ExistingRepository,
)

from registrations.models import Employee, Registration

from tasks.models import Task

User: Employee = get_user_model()


class GetProjectsStaffStatusTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff_password = "hunter1"
        cls.staff = User.objects._create_user(
            github_id=0, is_staff=True, is_superuser=False
        )

        cls.view_permission = Permission.objects.get(codename="view_project")
        cls.staff.user_permissions.add(cls.view_permission)

        cls.sem = Semester.objects.get_or_create_current_semester()
        cls.project = Project.objects.create(
            name="cooper",
            slug="cooper",
            semester=cls.sem,
        )

    def setUp(self):
        site = AdminSite
        self.project_admin = ProjectAdmin(Project, site)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_github_sync_all_button_hidden_without_permission(self):
        response = self.client.get(
            reverse("admin:projects_project_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(
            response, "Synchronize projects of the current semester to GitHub"
        )

    def test_sync_all_link_denied_without_permission(self):
        """
        A staff user can still try and sync using the link,
        but that is prevented in the backend. This is tested here.
        """
        backup = self.project_admin.synchronise_to_GitHub
        self.project_admin.synchronise_to_GitHub = MagicMock()

        response = self.client.get("/admin/projects/project/sync-to-github/")
        # expect Permission Denied
        self.assertEqual(response.status_code, 403)
        self.project_admin.synchronise_to_GitHub.assert_not_called()

        self.project_admin.synchronise_to_GitHub = backup

    def test_github_sync_action_hidden_in_ui(self):
        response = self.client.get(
            reverse("admin:projects_project_changelist")
        )
        self.assertEqual(response.status_code, 200)

        self.assertNotContains(
            response,
            'value="synchronise_to_GitHub"',
        )

    @patch("projects.admin.GitHubSync")
    def test_github_sync_action_denied_with_no_perm(self, mock_sync_class):
        mock_sync = MagicMock()

        mock_sync_class.return_value = mock_sync

        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {
                "action": "synchronise_to_GitHub",
                "_selected_action": [self.project.pk],
            },
        )

        mock_sync_class.assert_not_called()

        # Even though we want to see 403 (Permission Denied),
        # we are instead redirected back to changelist in case
        # of failure. We are redirected to the task bar if we
        # succeed, so we check that it did not happen.
        self.assertNotIn("task", response.url)


class RepositoryInlinesTest(TestCase):
    """
    Instantiate inlines and test their querysets.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "mccree"
        cls.admin = User.objects.create_superuser(
            github_id=0, github_username="admin"
        )

        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.project = Project.objects.create(
            name="test",
            slug="test",
            semester=cls.semester,
        )

        cls.new_repo = Repository.objects.create(
            name="new-repo",
            github_repo_id=None,
            project=cls.project,
        )

        cls.existing_repo = Repository.objects.create(
            name="existing-repo",
            github_repo_id=6969,
            project=cls.project,
        )

    def setUp(self):
        self.site = AdminSite()

        self.request = RequestFactory().get("/")
        self.request.user = self.admin

    def test_new_repository_inline_queryset(self):
        inline = NewRepositoryInline(
            Project,
            self.site,
        )

        self.assertIn(
            "github_repo_id",
            inline.get_readonly_fields(request=self.request),
        )

        qs = inline.get_queryset(self.request)

        self.assertIn(self.new_repo, qs)
        self.assertNotIn(self.existing_repo, qs)

    def test_existing_repository_inline_queryset(self):
        inline = ExistingRepositoryInline(
            Project,
            self.site,
        )

        qs = inline.get_queryset(self.request)

        self.assertNotIn(self.new_repo, qs)
        self.assertIn(self.existing_repo, qs)


class FetchRepoTest(TestCase):
    """
    Tests for the "/fetch-repo" path of the Project admin.
    """

    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "punk2008"
        cls.admin = User.objects.create_superuser(
            github_id=0, github_username="admin"
        )

        cls.url = "/admin/projects/project/fetch-repo/?github_repo_id="

    def setUp(self):
        site = AdminSite
        self.project_admin = ProjectAdmin(Project, site)
        self.client = Client()
        self.client.force_login(self.admin)

    def test_missing_github_repo_id(self):
        response = self.client.get("/admin/projects/project/fetch-repo/")

        self.assertEqual(response.status_code, 400)

        self.assertJSONEqual(
            response.content,
            {"error": "missing github_repo_id"},
        )

    def test_non_integer_github_repo_id(self):
        response = self.client.get(
            "/admin/projects/project/fetch-repo/?github_repo_id=abc"
        )

        self.assertEqual(response.status_code, 400)

        self.assertJSONEqual(
            response.content,
            {"error": "github_repo_id must be an integer"},
        )

    @patch("projects.admin.GitHubAPITalker")
    def test_repository_not_found(self, mock_talker_class):
        mock_talker = MagicMock()
        mock_talker.get_repo.side_effect = UnknownObjectException(
            status=404,
            data={},
            headers={},
        )

        mock_talker_class.return_value = mock_talker

        response = self.client.get(
            "/admin/projects/project/fetch-repo/?github_repo_id=11"
        )

        self.assertEqual(response.status_code, 404)

        self.assertJSONEqual(
            response.content,
            {"error": "repository with provided id does not exist"},
        )

    @patch("projects.admin.GitHubAPITalker")
    def test_github_exception(self, mock_talker_class):
        mock_talker = MagicMock()

        err_text = "im bout to bomb this whole ms GitHub"
        status = 507
        mock_talker.get_repo.side_effect = GithubException(
            status=status,
            message=err_text,
        )

        mock_talker_class.return_value = mock_talker

        response = self.client.get(
            "/admin/projects/project/fetch-repo/?github_repo_id=1703"
        )

        self.assertEqual(response.status_code, status)

        self.assertJSONEqual(
            response.content,
            {
                "error": err_text,
            },
        )

    @patch("projects.admin.GitHubAPITalker")
    def test_success_not_archived(self, mock_talker_class):
        repo = MagicMock()
        repo.name = "test-repo"
        repo.private = True
        repo.archived = False

        mock_talker = MagicMock()
        mock_talker.get_repo.return_value = repo

        mock_talker_class.return_value = mock_talker

        response = self.client.get(
            "/admin/projects/project/fetch-repo/?github_repo_id=1999"
        )

        self.assertEqual(response.status_code, 200)

        self.assertJSONEqual(
            response.content,
            {
                "name": "test-repo",
                "private": True,
                "archived": Repository.Archived.NOT_ARCHIVED,
            },
        )

    @patch("projects.admin.GitHubAPITalker")
    def test_fetch_repo_success_archived(self, mock_talker_class):
        repo = MagicMock()
        repo.name = "test-repo"
        repo.private = False
        repo.archived = True

        mock_talker = MagicMock()
        mock_talker.get_repo.return_value = repo

        mock_talker_class.return_value = mock_talker

        response = self.client.get(
            "/admin/projects/project/fetch-repo/?github_repo_id=123"
        )

        self.assertEqual(response.status_code, 200)

        self.assertJSONEqual(
            response.content,
            {
                "name": "test-repo",
                "private": False,
                "archived": Repository.Archived.CONFIRMED,
            },
        )


class GetProjectsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(
            github_id=0, github_username="admin"
        )

        cls.semester = Semester.objects.create(
            year=2020, season=Semester.SPRING
        )

        cls.project = Project.objects.create(
            name="test", slug="test", semester=cls.semester
        )
        cls.project_archived = Project.objects.create(
            name="test-archived", slug="test-archived", semester=cls.semester
        )

        cls.manager = User.objects.create(
            github_id=1,
            github_username="manager",
            first_name="John",
            last_name="Doe",
            student_number="s1234567",
        )
        reg = Registration.objects.create(
            user=cls.manager,
            semester=cls.semester,
            course=Course.objects.sdm(),
            preference1=cls.project,
            dev_experience=Registration.EXPERIENCE_ADVANCED,
        )
        reg.add_project(cls.project)

        cls.repo1 = Repository.objects.create(
            name="testrepo1", project=cls.project
        )
        cls.repo2 = Repository.objects.create(
            name="testrepo2", project=cls.project
        )
        cls.repo_archived = Repository.objects.create(
            name="testrepo-archived",
            project=cls.project_archived,
            is_archived=Repository.Archived.CONFIRMED,
        )

        cls.mailing_list = MailingList.objects.create(
            address="test", description=cls.project.description
        )

        cls.task = Task.objects.create(
            total=1,
            completed=0,
            fail=False,
            success_message="success",
            redirect_url=reverse("admin:projects_project_changelist"),
        )

    def setUp(self):
        site = AdminSite
        self.project_admin = ProjectAdmin(Project, site)
        request_factory = RequestFactory()
        self.request = request_factory.get(
            reverse("admin:projects_project_changelist")
        )
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
        response = self.client.get(
            reverse("admin:projects_project_change", args=(self.project.id,))
        )
        self.assertEqual(response.status_code, 200)

    def test_get_add(self):
        response = self.client.get(reverse("admin:projects_project_add"))
        self.assertEqual(response.status_code, 200)

    @freeze_time("2020-06-01")
    def test_form_save_new(self):
        response = self.client.post(
            reverse("admin:projects_project_add"),
            {
                "name": "Test project",
                "slug": "test-project",
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

    def test_sync_button_shown_with_permission(self):
        """
        The tests are set up such that the user making the
        requests is a superuser, hence the button should
        appear for them.
        """
        response = self.client.get(
            reverse("admin:projects_project_changelist")
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Synchronize projects of the current semester to GitHub"
        )

    def test_github_sync_action_appears_in_ui_with_permission(self):
        response = self.client.get(
            reverse("admin:projects_project_changelist")
        )
        self.assertEqual(response.status_code, 200)

        self.assertContains(
            response,
            'value="synchronise_to_GitHub"',
        )

    @patch("projects.admin.GitHubSync")
    def test_github_sync_action_allowed_with_perm(self, mock_sync_class):
        task_id = 1

        mock_sync = MagicMock()
        mock_sync.perform_asynchronous_sync.return_value = task_id

        mock_sync_class.return_value = mock_sync

        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {
                "action": "synchronise_to_GitHub",
                "_selected_action": [self.project.pk],
            },
            follow=False,
        )
        expected_redirect_url = reverse(
            "admin:progress_bar", kwargs={"task": task_id}
        )

        self.assertEqual(response.status_code, 302)  # redirects
        self.assertEqual(response.url, expected_redirect_url)

    def test_create_mail_is_valid(self):
        p1 = Project.objects.create(
            name="p1",
            semester=self.semester,
            description="test1",
            slug="p1",
        )

        sem2 = Semester.objects.create(year=2030, season=Semester.SPRING)
        p2 = Project.objects.create(
            name="p23352135no/fe",
            semester=sem2,
            description="test2",
        )

        self.client.post(
            reverse("admin:projects_project_changelist"),
            {
                ACTION_CHECKBOX_NAME: [p1.pk, p2.pk],
                "action": "create_mailing_lists",
                "index": 0,
            },
        )

        self.assertTrue(MailingList.objects.filter(projects=p1).exists())
        self.assertTrue(MailingList.objects.filter(projects=p2).exists())

    def test_create_mailing_lists(self):
        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {
                ACTION_CHECKBOX_NAME: [self.project.pk],
                "action": "create_mailing_lists",
                "index": 0,
            },
        )

        self.assertEqual(response.status_code, 302)

    def test_projectteam_added_in_mailing_list(self):
        pa = ProjectAdmin(ProjectAdminForm, admin_site=None)

        sem1 = Semester.objects.create(year=2024, season=1)
        sem2 = Semester.objects.create(year=2019, season=0)
        course = Course.objects.create(name="testcourse")

        test_project = Project.objects.create(
            name="test_project",
            semester=sem1,
            description="1",
            slug="test_project",
        )
        test_project2 = Project.objects.create(
            name="test_project2", semester=sem2, description="2"
        )
        test_user1 = User.objects.create(github_id=123, github_username="Bob")
        test_user2 = User.objects.create(
            github_id=1234, github_username="Nick"
        )
        test_user3 = User.objects.create(
            github_id=1235, github_username="James"
        )

        reg1 = Registration.objects.create(
            user=test_user1,
            semester=sem1,
            course=course,
            preference1=test_project,
            dev_experience=1,
            is_international=False,
        )
        reg1.add_project(test_project)
        reg2 = Registration.objects.create(
            user=test_user2,
            semester=sem2,
            course=course,
            preference1=test_project,
            dev_experience=1,
            is_international=False,
        )
        reg2.add_project(test_project)

        reg3 = Registration.objects.create(
            user=test_user3,
            semester=sem1,
            course=course,
            preference1=test_project,
            dev_experience=1,
            is_international=False,
        )
        reg3.add_project(test_project)

        pa.create_mailing_lists(self.request, [test_project, test_project2])

        messages.success.assert_called()

        lists = MailingList.objects.all()
        user_list = []

        for mailing_list in lists:
            reg = Registration.objects.all()
            for r in reg:
                if (
                    mailing_list.address
                    == r.get_projects().first().generate_email()
                ):
                    user_list.append(r.user.github_id)

        self.assertIn(test_user1.github_id, user_list)
        self.assertIn(test_user2.github_id, user_list)
        self.assertIn(test_user3.github_id, user_list)

    def test_non_duplicate_project_in_mailing_list(self):
        pa = ProjectAdmin(ProjectAdminForm, admin_site=None)
        sem1 = Semester.objects.create(year=2024, season=1)
        test_project = Project.objects.create(
            name="test_project", semester=sem1, description="1"
        )

        pa.create_mailing_lists(self.request, [test_project])
        pa.create_mailing_lists(self.request, [test_project])

        messages.error.assert_called()

    def test_synchronise_projects_to_GitHub(self):
        all_projects = Project.objects.all()
        self.sync_mock.perform_asynchronous_sync.return_value = self.task.id
        with patch("projects.admin.GitHubSync", self.github_mock):
            self.project_admin.synchronise_to_GitHub(
                self.request, all_projects
            )
        self.github_mock.assert_called_once()
        self.assertEqual(
            list(self.github_mock.call_args.args[0]),
            list(Project.objects.all()),
        )
        self.sync_mock.perform_asynchronous_sync.assert_called_once()

    def test_sync_button_has_effect(self):
        backup = self.project_admin.synchronise_to_GitHub
        self.project_admin.synchronise_to_GitHub = MagicMock()

        response = self.client.get("/admin/projects/project/sync-to-github/")
        # expect no exception thrown
        self.assertNotEqual(response.status_code, 403)

        self.project_admin.synchronise_to_GitHub = backup

    @freeze_time("2020-06-01")
    def test_synchronise_current_projects_to_GitHub(self):
        original_sync_action = self.project_admin.synchronise_to_GitHub
        self.project_admin.synchronise_to_GitHub = MagicMock()
        self.project_admin.synchronise_current_projects_to_GitHub(self.request)
        self.project_admin.synchronise_to_GitHub.assert_called_once()
        args = self.project_admin.synchronise_to_GitHub.call_args.args
        self.assertEqual(args[0], self.request)
        self.assertEqual(len(args[1]), 1)
        self.assertIn(self.project, args[1])
        self.assertNotIn(self.project_archived, args[1])
        self.project_admin.synchronise_to_GitHub = original_sync_action

    def test_archive_all_repositories(self):
        self.project_admin.archive_all_repositories(
            self.request, Project.objects.all()
        )
        self.repo1.refresh_from_db()
        self.repo2.refresh_from_db()
        self.repo_archived.refresh_from_db()
        self.assertTrue(self.repo1.is_archived)
        self.assertTrue(self.repo2.is_archived)
        self.assertTrue(self.repo_archived.is_archived)

    def test_repository_deleted(self):
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
                "repository_set-0-DELETE": True,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)

    def test_repository_archived_confirmed(self):
        self.repo1.is_archived = Repository.Archived.CONFIRMED
        self.repo1.save()
        response = self.client.get(
            reverse("admin:projects_project_change", args=[self.project.id])
        )
        self.assertEqual(response.status_code, 200)

    def test_is_archived(self):
        self.assertTrue(self.project_admin.is_archived(self.project_archived))
        self.assertFalse(self.project_admin.is_archived(self.project))

    def test_archived_filter__archived(self):
        archived_filter = ProjectAdminArchivedFilter(
            self.request, {"repo_archived": "1"}, Project, ProjectAdmin
        )
        result = archived_filter.queryset(self.request, Project.objects.all())
        self.assertEqual(result.count(), 1)
        self.assertIn(self.project_archived, result)

    def test_archived_filter__not_archived(self):
        archived_filter = ProjectAdminArchivedFilter(
            self.request, {"repo_archived": "0"}, Project, ProjectAdmin
        )
        result = archived_filter.queryset(self.request, Project.objects.all())
        self.assertEqual(result.count(), 1)
        self.assertIn(self.project, result)

    def test_archived_filter__all(self):
        archived_filter = ProjectAdminArchivedFilter(
            self.request, {}, Project, ProjectAdmin
        )
        result = archived_filter.queryset(self.request, Project.objects.all())
        self.assertEqual(result.count(), 2)
        self.assertIn(self.project, result)
        self.assertIn(self.project_archived, result)

    def test_export_project_members(self):
        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {
                ACTION_CHECKBOX_NAME: [self.project.pk],
                "action": "export_project_members",
                "index": 0,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            '"Project","First name","Last name","Student number","GitHub username","Role"',
        )
        self.assertContains(
            response,
            f'"{self.project.name}","{self.manager.first_name}","{self.manager.last_name}",'
            f'"{self.manager.student_number}","{self.manager.github_username}"',
        )

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_updates_slug_on_creation(self, mock_sync):
        """Test that slug is generated from project name and semester year on creation."""
        project = Project(
            name="Test Project",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        form = MagicMock()

        self.project_admin.save_model(
            self.request, project, form, change=False
        )

        project.refresh_from_db()
        self.assertEqual(project.slug, "test-project-2020")

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_updates_slug_on_name_change(self, mock_sync):
        """Test that slug is updated when project name changes."""
        project = Project.objects.create(
            name="Old Name",
            slug="old-name-2020",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        project.name = "New Name"
        form = MagicMock()

        self.project_admin.save_model(self.request, project, form, change=True)

        project.refresh_from_db()
        self.assertEqual(project.slug, "new-name-2020")

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_updates_slug_on_semester_change(self, mock_sync):
        """Test that slug is updated when semester year changes."""
        new_semester = Semester.objects.create(
            year=2021, season=Semester.SPRING
        )
        project = Project.objects.create(
            name="Test Project",
            slug="test-project-2020",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        project.semester = new_semester
        form = MagicMock()

        self.project_admin.save_model(self.request, project, form, change=True)

        project.refresh_from_db()
        self.assertEqual(project.slug, "test-project-2021")

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_does_not_update_slug_if_unchanged(self, mock_sync):
        """Test that slug is not updated if it doesn't need to change."""
        project = Project.objects.create(
            name="Test Project",
            slug="test-project-2020",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        original_slug = project.slug
        form = MagicMock()

        self.project_admin.save_model(self.request, project, form, change=True)

        project.refresh_from_db()
        self.assertEqual(project.slug, original_slug)

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_creates_default_repository(self, mock_sync):
        """Test that a default repository is created when default_repo is True and no repos exist."""
        project = Project(
            name="Test Project",
            slug="test-project-2020",
            semester=self.semester,
            description="Test description",
            default_repo=True,
        )
        form = MagicMock()

        self.project_admin.save_model(
            self.request, project, form, change=False
        )

        project.refresh_from_db()
        self.assertEqual(project.repository_set.count(), 1)
        self.assertEqual(
            project.repository_set.first().name, "test-project-2020"
        )
        self.assertFalse(project.default_repo)

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_does_not_create_repo_if_default_repo_false(
        self, mock_sync
    ):
        """Test that no repository is created when default_repo is False."""
        project = Project(
            name="Test Project",
            slug="test-project-2020",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        form = MagicMock()

        self.project_admin.save_model(
            self.request, project, form, change=False
        )

        project.refresh_from_db()
        self.assertEqual(project.repository_set.count(), 0)

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_with_special_characters_in_name(self, mock_sync):
        """Test that slug is properly generated with special characters in project name."""
        project = Project(
            name="Test & Project!",
            semester=self.semester,
            description="Test description",
            default_repo=False,
        )
        form = MagicMock()

        self.project_admin.save_model(
            self.request, project, form, change=False
        )

        project.refresh_from_db()
        # slugify converts special characters appropriately
        self.assertEqual(project.slug, "test-project-2020")

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_new_obj_githubsync_called(self, mock_sync):
        project = Project(
            name="idk atp",
            semester=self.semester,
            description="wsg",
            default_repo=False,
        )
        form = MagicMock()  # does not matter in this case

        self.project_admin.save_model(
            self.request, project, form, change=False
        )

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_existing_obj_form_triggers_sync(self, mock_sync):
        project = Project.objects.create(
            name="sanchez",
            semester=self.semester,
            description="none",
            default_repo=False,
        )
        form = MagicMock()
        form.changed_data = ["name"]

        self.project_admin.save_model(self.request, project, form, change=True)

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_save_model_existing_obj_form_does_not_trigger_sync(
        self, mock_sync
    ):
        project = Project.objects.create(
            name="bird person",
            semester=self.semester,
            description="none",
            default_repo=False,
        )
        form = MagicMock()
        form.changed_data = ["comments"]

        self.project_admin.save_model(self.request, project, form, change=True)

        mock_sync.assert_not_called()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_no_sync_when_no_inlines_added(self, mock_sync):
        form = MagicMock()
        form.instance = self.project

        repo_formset = MagicMock()
        repo_formset.model = NewRepository
        repo_formset.new_objects = []
        repo_formset.changed_objects = []
        repo_formset.deleted_objects = []

        self.project_admin.save_related(
            request=MagicMock(),
            form=form,
            formsets=[repo_formset],
            change=True,
        )

        mock_sync.assert_not_called()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_no_sync_on_mailing_lists_added(self, mock_sync):
        form = MagicMock()
        form.instance = self.project

        ml_formset = MagicMock()
        ml_formset.model = MailingList.projects.through
        ml_formset.new_objects = [MagicMock()]
        ml_formset.changed_objects = []
        ml_formset.deleted_objects = []

        self.project_admin.save_related(
            request=self.request,
            form=form,
            formsets=[ml_formset],
            change=True,
        )

        mock_sync.assert_not_called()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_sync_on_repo_added(self, mock_sync):
        form = MagicMock()
        form.instance = self.project

        repo_formset = MagicMock()
        repo_formset.model = NewRepository
        repo_formset.new_objects = [MagicMock()]
        repo_formset.changed_objects = []
        repo_formset.deleted_objects = []

        self.project_admin.save_related(
            request=self.request,
            form=form,
            formsets=[repo_formset],
            change=True,
        )

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_sync_on_repo_deleted(self, mock_sync):
        form = MagicMock()
        form.instance = self.project

        repo_formset = MagicMock()
        repo_formset.model = ExistingRepository
        repo_formset.new_objects = []
        repo_formset.changed_objects = []
        repo_formset.deleted_objects = [MagicMock()]

        self.project_admin.save_related(
            request=MagicMock(),
            form=form,
            formsets=[repo_formset],
            change=True,
        )

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_sync_on_existing_repo_changed(self, mock_sync):
        form = MagicMock()
        form.instance = self.project

        repo_formset = MagicMock()
        repo_formset.model = ExistingRepository
        repo_formset.new_objects = []
        repo_formset.changed_objects = [MagicMock()]
        repo_formset.deleted_objects = []

        self.project_admin.save_related(
            request=MagicMock(),
            form=form,
            formsets=[repo_formset],
            change=True,
        )

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_sync_on_project_delete(self, mock_sync):
        self.project_admin.delete_model(
            self.request,
            self.project,
        )

        mock_sync.assert_called_once()

    @patch.object(ProjectAdmin, "synchronise_to_GitHub")
    def test_sync_on_bulk_delete(self, mock_sync):
        # still counts as bulk
        queryset = Project.objects.all()

        self.project_admin.delete_queryset(
            self.request,
            queryset,
        )

        mock_sync.assert_called_once_with(self.request, queryset)
