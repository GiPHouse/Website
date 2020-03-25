from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock

from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, RequestFactory, TestCase

from github import GithubException

from courses.models import Course, Semester

from projects import githubsync
from projects.admin import ProjectAdmin
from projects.models import Project, Repository

from registrations.models import Employee, Registration

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
        githubsync.talker._gi.get_access_token = MagicMock()
        githubsync.talker._github = MagicMock()
        self.old_talker = githubsync.talker
        self.talker = githubsync.GitHubAPITalker()
        self.talker._access_token = MagicMock()
        self.talker._access_token.expires_at = datetime.now() + timedelta(hours=1)
        self.talker.update_team = MagicMock()
        self.talker.update_repo = MagicMock()
        self.talker.sync_team_member = MagicMock(return_value=1)
        self.talker.remove_users_not_in_team = MagicMock(return_value=(1, []))
        self.talker.create_team = MagicMock(return_value=MagicMock(id=1234))
        self.talker.create_repo = MagicMock(return_value=MagicMock(id=1234))
        self.talker.remove_team = MagicMock()
        self.talker.archive_repo = MagicMock()
        githubsync.talker = self.talker
        self.old_error = messages.error
        self.old_warning = messages.warning
        self.old_success = messages.success
        messages.error = MagicMock()
        messages.warning = MagicMock()
        messages.success = MagicMock()

    def tearDown(self):
        githubsync.talker = self.old_talker
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

    def test_csv_export(self):
        response = self.client.post(
            reverse("admin:projects_project_changelist"),
            {ACTION_CHECKBOX_NAME: [self.project.pk], "action": "export_addresses_csv", "index": 0},
        )
        self.assertEqual(response.status_code, 200)

    def test_create_or_update_team__create(self):
        self.project.github_team_id = None
        self.project.save()
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                team_created, members_invited, users_removed = self.project_admin.create_or_update_team(
                    self.request, self.project
                )

        self.talker.create_team.assert_called_once_with(self.project)
        self.talker.update_team.not_called()
        self.talker.sync_team_member.assert_called_once_with(self.manager, self.project)
        self.talker.remove_users_not_in_team.called_once_with(self.project)
        self.assertTrue(team_created)
        self.assertEqual(members_invited, 1)
        self.assertEqual(users_removed, 1)

    def test_create_or_update_team__create_error(self):
        self.project.github_team_id = None
        self.project.save()
        self.talker.create_team = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.talker.sync_team_member = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.talker.remove_users_not_in_team = MagicMock(
            side_effect=GithubException(status=mock.Mock(status=404), data="abc")
        )
        messages.error = MagicMock()
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                team_created, members_invited, users_removed = self.project_admin.create_or_update_team(
                    self.request, self.project
                )
        self.assertEqual(messages.error.call_count, 3)  # TODO check content of message
        self.talker.create_team.assert_called_once_with(self.project)
        self.talker.update_team.not_called()
        self.talker.sync_team_member.assert_called_once_with(self.manager, self.project)
        self.talker.remove_users_not_in_team.called_once_with(self.project)
        self.assertFalse(team_created)
        self.assertEqual(members_invited, 0)
        self.assertEqual(users_removed, 0)

    def test_create_or_update_team__update(self):
        self.project.github_team_id = 1234
        self.project.save()
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                team_created, members_invited, users_removed = self.project_admin.create_or_update_team(
                    self.request, self.project
                )

        self.talker.create_team.not_called()
        self.talker.update_team.assert_called_once_with(self.project)
        self.talker.sync_team_member.assert_called_once_with(self.manager, self.project)
        self.talker.remove_users_not_in_team.called_once_with(self.project)
        self.assertFalse(team_created)
        self.assertEqual(members_invited, 1)
        self.assertEqual(users_removed, 1)

    def test_create_or_update_team__update_error(self):
        self.project.github_team_id = 1234
        self.project.save()
        self.talker.update_team = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.talker.sync_team_member = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.talker.remove_users_not_in_team = MagicMock(return_value=(1, ["Piet"]))
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                team_created, members_invited, users_removed = self.project_admin.create_or_update_team(
                    self.request, self.project
                )
        self.assertEqual(messages.error.call_count, 3)  # TODO check content of message
        self.talker.create_team.not_called()
        self.talker.update_team.assert_called_once_with(self.project)
        self.talker.sync_team_member.assert_called_once_with(self.manager, self.project)
        self.talker.remove_users_not_in_team.called_once_with(self.project)
        self.assertFalse(team_created)
        self.assertEqual(members_invited, 0)
        self.assertEqual(users_removed, 1)

    def test_create_or_update_repos__create(self):
        self.repo.github_repo_id = None
        self.repo.save()
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                new_repos_created = self.project_admin.create_or_update_repos(self.request, self.project)
        self.talker.create_repo.assert_called_once_with(self.repo)
        self.talker.update_repo.assert_not_called()
        self.assertEqual(new_repos_created, 1)

    def test_create_or_update_repos__create_error(self):
        self.repo.github_repo_id = None
        self.repo.save()
        self.talker.create_repo = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                new_repos_created = self.project_admin.create_or_update_repos(self.request, self.project)
        messages.error.assert_called_once()  # TODO check content of message
        self.talker.create_repo.assert_called_once_with(self.repo)
        self.talker.update_repo.assert_not_called()
        self.assertEqual(new_repos_created, 0)

    def test_create_or_update_repos__update(self):
        self.repo.github_repo_id = 4321
        self.repo.save()
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                new_repos_created = self.project_admin.create_or_update_repos(self.request, self.project)
        self.talker.update_repo.assert_called_once_with(self.repo)
        self.talker.create_repo.assert_not_called()
        self.assertEqual(new_repos_created, 0)

    def test_create_or_update_repos__update_error(self):
        self.repo.github_repo_id = 4321
        self.repo.save()
        self.talker.update_repo = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                new_repos_created = self.project_admin.create_or_update_repos(self.request, self.project)
        messages.error.assert_called_once()  # TODO check content of message
        self.talker.update_repo.assert_called_once_with(self.repo)
        self.talker.create_repo.assert_not_called()
        self.assertEqual(new_repos_created, 0)

    def test_archive_project__repo_unarchived(self):
        self.repo_archived.github_repo_id = 123456789
        self.repo_archived.save()
        self.talker.archive_repo = MagicMock(return_value=True)
        result = self.project_admin.archive_project(self.request, self.project_archived)
        self.talker.archive_repo.assert_called_once_with(self.repo_archived)
        self.assertEqual(result, 1)

    def test_archive_project__repo_already_archived(self):
        self.repo_archived.github_repo_id = 123456789
        self.repo_archived.save()
        self.talker.archive_repo = MagicMock(return_value=False)
        result = self.project_admin.archive_project(self.request, self.project_archived)
        self.talker.archive_repo.assert_called_once_with(self.repo_archived)
        self.assertEqual(result, 0)

    def test_archive_project__uncreated_repo(self):
        self.repo_archived.github_repo_id = None
        self.project_archived.save()
        result = self.project_admin.archive_project(self.request, self.project_archived)
        self.talker.archive_repo.assert_not_called()
        messages.warning.assert_called_once()  # TODO check content of message
        self.assertEqual(result, 0)

    def test_archive_project__repo_error(self):
        self.repo_archived.github_repo_id = 123456789
        self.repo_archived.save()
        self.talker.archive_repo = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.project_admin.archive_project(self.request, self.project_archived)
        messages.error.assert_called_once()  # TODO check content of message

    def test_archive_project__team(self):
        self.project_archived.github_team_id = 987654321
        self.project_archived.save()
        self.project_admin.archive_project(self.request, self.project_archived)
        self.talker.remove_team.assert_called_once_with(self.project_archived)
        self.assertIsNone(self.project_archived.github_team_id)

    def test_archive_project__uncreated_team(self):
        self.project_archived.github_team_id = None
        self.project_archived.save()
        self.project_admin.archive_project(self.request, self.project_archived)
        self.talker.remove_team.assert_not_called()
        messages.warning.assert_called()  # Can be called multiple times, because repo's can fail too,
        # TODO check content of message

    def test_archive_project__team_error(self):
        self.project_archived.github_team_id = 987654321
        self.talker.remove_team = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        self.project_admin.archive_project(self.request, self.project_archived)
        messages.error.assert_called_once()  # TODO check content of message

    def test_synchronise_to_GitHub__create(self):
        self.project_admin.create_or_update_team = MagicMock(return_value=(True, 1, 1))
        self.project_admin.create_or_update_repos = MagicMock(return_value=1)
        self.project_admin.synchronise_to_GitHub(self.request, Project.objects.all())
        messages.success.assert_called_once()  # TODO check content of message
        self.project_admin.create_or_update_team.assert_called_once_with(self.request, self.project)
        self.project_admin.create_or_update_repos.assert_called_once_with(self.request, self.project)

    def test_synchronise_to_GitHub__update(self):
        self.project_admin.create_or_update_team = MagicMock(return_value=(False, 1, 1))
        self.project_admin.create_or_update_repos = MagicMock(return_value=1)
        self.project_admin.synchronise_to_GitHub(self.request, Project.objects.all())
        messages.success.assert_called_once()  # TODO check content of message
        self.project_admin.create_or_update_team.assert_called_once_with(self.request, self.project)
        self.project_admin.create_or_update_repos.assert_called_once_with(self.request, self.project)

    def test_synchronise_to_GitHub__archive(self):
        self.project_admin.archive_project = MagicMock(return_value=1)
        self.project_admin.synchronise_to_GitHub(self.request, Project.objects.all())
        self.project_admin.archive_project.assert_called_once_with(self.request, self.project_archived)

    def test_synchronise_all_projects_to_GitHub(self):
        self.project_admin.synchronise_to_GitHub = MagicMock()
        self.project_admin.create_or_update_team = MagicMock(return_value=(True, 1, 1))
        self.project_admin.synchronise_all_projects_to_GitHub(self.request)
        self.project_admin.synchronise_to_GitHub.assert_called_once()
        args = self.project_admin.synchronise_to_GitHub.call_args.args
        self.assertEqual(args[0], self.request)
        self.assertEqual(args[1].count(), 2)
        self.assertIn(self.project, args[1])
