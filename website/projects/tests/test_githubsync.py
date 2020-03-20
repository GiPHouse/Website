from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock

from django.conf import settings
from django.test import TestCase

from github import GithubException

from courses.models import Semester

from projects import githubsync
from projects.models import Project, Repository

from registrations.models import Employee


class GitHubAPITalkerTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Setup test data to use in these tests."""
        cls.organization = "AGitHubOrganizationName"
        cls.app_id = 12345
        cls.installation_id = 1234567
        cls.semester = Semester(year=2020, season=Semester.FALL)
        cls.project1 = Project(name="test1", github_team_id="87654321", semester=cls.semester)
        cls.repo1 = Repository(name="test-repo1", github_repo_id="987654321", project=cls.project1)
        cls.employee1 = Employee(github_username="testgithubuser")

    def setUp(self):
        """Create a mock pygithub object to talk with."""
        githubsync.talker._gi.get_access_token = MagicMock()
        githubsync.talker._github = MagicMock()
        self.talker = githubsync.GitHubAPITalker()
        self.talker._access_token = MagicMock()
        self.talker._access_token.expires_at = datetime.now() + timedelta(hours=1)
        self.talker._organization = MagicMock()
        self.talker._organization.create_team = MagicMock()
        self.talker._github = MagicMock()

    def tearDown(self):
        """Remove objects after a test is performed."""
        del self.talker

    def test_singleton(self):
        """Test that normally only one instance of GitHubAPITalker can exist."""
        talker1 = githubsync.talker
        talker2 = githubsync.talker
        self.assertEqual(talker1, talker2)

    def test_renew_access_token_if_required__unexpired(self):
        """Test if when requesting an unexpired token, nothing happens."""
        self.talker._gi.get_access_token = MagicMock()
        self.talker._github = MagicMock()
        self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_not_called()
        self.talker._github.get_organization.assert_not_called()

    def test_renew_access_token_if_required__expired(self):
        """Test if when requesting an expired token, a new token is requested."""
        self.talker._access_token.expires_at = datetime.now() - timedelta(hours=1)
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_renew_access_token_if_required__almost_expired(self):
        """Test if when requesting an almost expiring token, a new token is requested."""
        self.talker._access_token.expires_at = datetime.now() + timedelta(seconds=30)
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_renew_access_token_if_required__no_token(self):
        """Test if when requesting a token when no token exists yet, a new token is requested."""
        self.talker._access_token = None
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_create_team(self):
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.create_team(self.project1)
        self.talker._organization.create_team.assert_called_once_with(
            "test1",
            description=f"Team for the GiPHouse project 'test1' for the 'Fall 2020' semester.",
            privacy="closed",
        )

    def test_update_team__incorrect_description(self):
        result = MagicMock()
        result.name = "test"
        result.description = "The wrong description"
        result.edit = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=result)
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.update_team(self.project1)
        result.edit.assert_called_once_with(
            name="test1", description=f"Team for the GiPHouse project 'test1' for the 'Fall 2020' semester."
        )

    def test_update_team__incorrect_team_name(self):
        result = MagicMock()
        result.name = "The wrong name"
        result.description = "Team for the GiPHouse project 'test1' for the 'Fall 2020' semester."
        result.edit = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=result)
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.update_team(self.project1)
        result.edit.assert_called_once_with(
            name="test1", description=f"Team for the GiPHouse project 'test1' for the 'Fall 2020' semester."
        )

    def test_update_team__all_correct(self):
        result = MagicMock()
        result.name = "test1"
        result.description = "Team for the GiPHouse project 'test1' for the 'Fall 2020' semester."
        result.edit = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=result)
        with mock.patch("github.MainClass.Github.__init__", return_value=None):
            with mock.patch("github.MainClass.Github.get_organization"):
                self.talker.update_team(self.project1)
        result.edit.assert_not_called()

    def test_create_repo(self):
        self.talker._organization.create_repo = MagicMock(return_value="ThisShouldBeAPyGithubRepo")

        mock_team = MagicMock()
        mock_team.add_to_repos = MagicMock()
        mock_team.set_repo_permission = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=mock_team)
        returned_repo = self.talker.create_repo(self.repo1)

        self.talker._organization.create_repo.assert_called_once_with(
            name=self.repo1.name, private=settings.GITHUB_REPO_PRIVATE
        )
        self.assertEquals(returned_repo, "ThisShouldBeAPyGithubRepo")
        mock_team.add_to_repos.assert_called_once_with(returned_repo)
        mock_team.set_repo_permission.assert_called_once_with(returned_repo, "admin")

    def test_update_repo__incorrect_name(self):
        github_repo = MagicMock()
        github_repo.name = "test-repo2"
        self.talker._github.get_repo = MagicMock(return_value=github_repo)

        github_team = MagicMock()
        github_team.has_in_repos = MagicMock(return_value=True)
        self.talker._organization.get_team = MagicMock(return_value=github_team)

        self.talker.update_repo(self.repo1)

        github_team.add_to_repos.assert_not_called()
        github_repo.edit.assert_called_once_with(name=self.repo1.name)

    def test_update_repo__incorrect_permissions(self):
        github_repo = MagicMock()
        github_repo.name = "test-repo1"
        self.talker._github.get_repo = MagicMock(return_value=github_repo)

        github_team = MagicMock()
        github_team.has_in_repos = MagicMock(return_value=False)
        self.talker._organization.get_team = MagicMock(return_value=github_team)

        self.talker.update_repo(self.repo1)

        github_team.add_to_repos.assert_called_once_with(github_repo)
        github_team.set_repo_permission.assert_called_once_with(github_repo, "admin")
        github_repo.edit.assert_not_called()

    def test_update_repo__all_correct(self):
        github_repo = MagicMock()
        github_repo.name = "test-repo1"
        self.talker._github.get_repo = MagicMock(return_value=github_repo)

        github_team = MagicMock()
        github_team.has_in_repos = MagicMock(return_value=True)
        self.talker._organization = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=github_team)

        self.talker.update_repo(self.repo1)

        github_team.add_to_repos.assert_not_called()
        github_repo.edit.assert_not_called()

    def test_sync_team_member__not_in_team(self):
        github_employee = MagicMock()
        github_employee.login = self.employee1.github_username
        self.project1.get_employees = MagicMock(return_value=[self.employee1])
        self.talker._github.get_user = MagicMock(return_value=github_employee)
        github_team = MagicMock()
        github_team.has_in_members = MagicMock(return_value=False)
        github_team.add_membership = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=github_team)

        return_value = self.talker.sync_team_member(self.employee1, self.project1)

        self.talker._github.get_user.assert_called_once_with(self.employee1.github_username)
        github_team.add_membership.assert_called_once_with(github_employee, role="member")
        self.assertTrue(return_value)

    def test_sync_team_member__already_in_team(self):
        github_employee = MagicMock()
        github_employee.login = self.employee1.github_username
        self.project1.get_employees = MagicMock(return_value=[self.employee1])
        self.talker._github.get_user = MagicMock(return_value=github_employee)
        github_team = MagicMock()
        github_team.has_in_members = MagicMock(return_value=True)
        github_team.add_membership = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=github_team)

        return_value = self.talker.sync_team_member(self.employee1, self.project1)

        self.talker._github.get_user.assert_called_once_with(self.employee1.github_username)
        github_team.add_membership.assert_not_called()
        self.assertFalse(return_value)

    def test_remove_users_not_in_team__employee(self):
        github_team = MagicMock()
        github_user = MagicMock()
        github_user.login = self.employee1.github_username
        github_team.get_members = MagicMock(return_value=[github_user])
        github_team.remove_membership = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=github_team)
        employees_queryset = MagicMock()
        employees_queryset.values_list = MagicMock(return_value=[(self.employee1.github_username,)])
        self.project1.get_employees = MagicMock(return_value=employees_queryset)

        users_removed, errors_removing = self.talker.remove_users_not_in_team(self.project1)

        github_team.remove_membership.assert_not_called()
        self.assertEquals(users_removed, 0)

    def test_remove_users_not_in_team__no_employee(self):
        github_team = MagicMock()
        github_user = MagicMock()
        github_user.login = "anunwanteduser"
        github_team.get_members = MagicMock(return_value=[github_user])
        github_team.remove_membership = MagicMock()
        self.talker._organization.get_team = MagicMock(return_value=github_team)
        employees_queryset = MagicMock()
        employees_queryset.values_list = MagicMock(return_value=[(self.employee1.github_username,)])
        self.project1.get_employees = MagicMock(return_value=employees_queryset)

        users_removed, errors_removing = self.talker.remove_users_not_in_team(self.project1)

        github_team.remove_membership.assert_called_once_with(github_user)
        self.assertEquals(users_removed, 1)

    def test_remove_users_not_in_team__exception(self):
        github_team = MagicMock()
        github_user = MagicMock()
        github_user.login = "anunwanteduser"
        github_team.get_members = MagicMock(return_value=[github_user])
        github_team.remove_membership = MagicMock(
            side_effect=GithubException(status=mock.Mock(status=404), data="abc")
        )
        self.talker._organization.get_team = MagicMock(return_value=github_team)
        employees_queryset = MagicMock()
        employees_queryset.values_list = MagicMock(return_value=[(self.employee1.github_username,)])
        self.project1.get_employees = MagicMock(return_value=employees_queryset)

        users_removed, errors_removing = self.talker.remove_users_not_in_team(self.project1)

        github_team.remove_membership.assert_called_once_with(github_user)
        self.assertEquals(errors_removing, [github_user.login])

    def test_username_exists(self):
        self.talker._github.get_user = MagicMock()
        result = self.talker.username_exists("Fake username")
        self.assertTrue(result)
        self.talker._github.get_user.assert_called_once_with("Fake username")

    def test_username_exists__not(self):
        self.talker._github.get_user = MagicMock(side_effect=GithubException(status=mock.Mock(status=404), data="abc"))
        result = self.talker.username_exists("Fake username")
        self.assertFalse(result)
        self.talker._github.get_user.assert_called_once_with("Fake username")
