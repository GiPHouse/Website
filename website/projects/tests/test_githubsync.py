from datetime import datetime, timedelta
from unittest import mock
from unittest.mock import MagicMock, patch

from django.test import TestCase

from github import GithubException, MainClass, UnknownObjectException

from courses.models import Course, Semester

from projects import githubsync
from projects.models import Project, ProjectToBeDeleted, Repository, RepositoryToBeDeleted

from registrations.models import Employee, Registration


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
        self.talker._github = MagicMock()

        self.old_github_init = MainClass.Github.__init__
        self.old_github_get_org = MainClass.Github.get_organization
        MainClass.Github.__init__ = MagicMock(return_value=None)
        MainClass.Github.get_organization = MagicMock()

    def tearDown(self):
        """Remove objects after a test is performed."""
        MainClass.Github.__init__ = self.old_github_init
        MainClass.Github.get_organization = self.old_github_get_org
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
        self.talker._access_token.expires_at = datetime.utcnow() - timedelta(hours=1)
        self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_renew_access_token_if_required__almost_expired(self):
        """Test if when requesting an almost expiring token, a new token is requested."""
        self.talker._access_token.expires_at = datetime.utcnow() + timedelta(seconds=30)
        self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_renew_access_token_if_required__no_token(self):
        """Test if when requesting a token when no token exists yet, a new token is requested."""
        self.talker._access_token = None
        self.talker.renew_access_token_if_required()
        self.talker._gi.get_access_token.assert_called_once_with(self.talker.installation_id)
        self.assertIsNotNone(self.talker._organization)

    def test_create_team(self):
        self.talker.create_team(self.project1)
        self.talker._organization.create_team.assert_called_once_with(
            "test1",
            description=f"Team for the GiPHouse project 'test1' for the 'Fall 2020' semester.",
            privacy="closed",
        )

    def test_create_repo(self):
        self.talker.create_repo(self.repo1)
        self.talker._organization.create_repo.assert_called_once_with(name="test-repo1", private=self.repo1.private)

    def test_get_team(self):
        self.talker.get_team(self.project1.github_team_id)
        self.talker._organization.get_team.assert_called_once_with(self.project1.github_team_id)

    def test_get_user(self):
        self.talker.get_user(self.employee1.github_username)
        self.talker._github.get_user.assert_called_once_with(self.employee1.github_username)

    def test_get_repo(self):
        self.talker.get_repo(self.repo1.github_repo_id)
        self.talker._github.get_repo.assert_called_once_with(self.repo1.github_repo_id)

    def test_remove_user(self):
        self.talker.remove_user(self.employee1.github_username)
        self.talker._organization.remove_from_members.assert_called_once_with(self.employee1.github_username)

    def test_get_role_of_user(self):
        user = MagicMock()
        self.talker.get_role_of_user(user)
        user.get_organization_membership.assert_called_once_with(self.talker._organization)

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

    def test_remove_all_teams_from_organization_owner(self):
        test_user = MagicMock()
        test_team = MagicMock()
        test_team.get_members = MagicMock(return_value=[test_user])
        self.talker.get_role_of_user = MagicMock(return_value="admin")
        self.talker.github_organization.get_teams = MagicMock(return_value=[test_team])
        self.talker.remove_user = MagicMock()
        self.talker.remove_all_teams_from_organization()
        self.talker.remove_user.assert_not_called()
        test_team.delete.assert_called_once()

    def test_remove_all_teams_from_organization_no_owner(self):
        test_user = MagicMock()
        test_team = MagicMock()
        test_team.get_members = MagicMock(return_value=[test_user])
        self.talker.get_role_of_user = MagicMock(return_value="user")
        self.talker.github_organization.get_teams = MagicMock(return_value=[test_team])
        self.talker.remove_user = MagicMock()
        self.talker.remove_all_teams_from_organization()
        self.talker.remove_user.assert_called_once_with(test_user)
        test_team.delete.assert_called_once()

    def test_delete_all_repositories_from_organization(self):
        test_repo = MagicMock()
        self.talker.github_organization.get_repos = MagicMock(return_value=[test_repo])
        self.talker.delete_all_repositories_from_organization()
        test_repo.delete.assert_called_once()


class GitHubSyncTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.semester = Semester.objects.create(year=2020, season=Semester.FALL)
        cls.project1 = Project.objects.create(name="test1", github_team_id="87654321", semester=cls.semester)
        cls.repo1 = Repository.objects.create(
            name="test-repo1", github_repo_id="987654321", project=cls.project1, private=True
        )
        cls.repo2 = Repository(name="test-repo2", github_repo_id="999999999", project=cls.project1, private=False)
        cls.employee1 = Employee.objects.create(github_username="testgithubuser", github_id=123456)
        Registration.objects.create(
            user=cls.employee1,
            project=cls.project1,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.se(),
            preference1=cls.project1,
            semester=cls.semester,
        )
        cls.exception = GithubException(status=MagicMock(status=404), data="abc")
        cls.repoToBeDeleted1 = RepositoryToBeDeleted.objects.create(github_repo_id=1122334455)
        cls.repoToBeDeleted2 = RepositoryToBeDeleted.objects.create(github_repo_id=5544332211)
        cls.projectToBeDeleted1 = ProjectToBeDeleted.objects.create(github_team_id=5566778899)
        cls.projectToBeDeleted2 = ProjectToBeDeleted.objects.create(github_team_id=9988776655)

    def setUp(self):
        self.project1.github_team_id = "87654321"
        self.project1.save()
        self.repo1.github_repo_id = "987654321"
        self.repo1.save()
        self.semester.is_archived = False
        self.semester.save()
        self.sync = githubsync.GitHubSync(Project.objects.all())

        self.talker = MagicMock()
        self.github_user = MagicMock()
        self.github_user.login = self.employee1.github_username
        self.github_team = MagicMock()
        self.github_team.name = self.project1.name
        self.github_team.description = self.project1.generate_team_description()
        self.github_team.get_members.return_value = [self.github_user]
        self.github_team.get_repo_permission.return_value = MagicMock(admin=True)
        self.github_team.has_in_repos.return_value = True
        self.github_repo = MagicMock()
        self.github_repo.name = "test-repo1"
        self.github_repo.private = True
        self.talker.get_user.return_value = self.github_user
        self.talker.get_team.return_value = self.github_team
        self.talker.get_repo.return_value = self.github_repo

        self.sync.github = self.talker

        self.logger = MagicMock()
        self.sync.logger = self.logger

    def setUpUser(self, login, role):
        self.github_user.login = login
        self.talker.get_role_of_user.return_value = role

    def mockSyncMembers(self):
        self.sync.sync_team_member = MagicMock()
        self.sync.remove_users_not_in_team = MagicMock()
        self.sync.update_team = MagicMock()
        self.sync.update_repo = MagicMock()
        self.sync.archive_repo = MagicMock()
        self.sync.remove_team = MagicMock()

    def assert_no_log(self):
        self.logger.info.assert_not_called()
        self.logger.warning.assert_not_called()
        self.logger.error.assert_not_called()
        self.assertFalse(self.sync.fail)

    def assert_info(self):
        self.logger.info.assert_called_once()
        self.logger.warning.assert_not_called()
        self.logger.error.assert_not_called()
        self.assertFalse(self.sync.fail)

    def assert_warning(self):
        self.logger.info.assert_not_called()
        self.logger.warning.assert_called_once()
        self.logger.error.assert_not_called()
        self.assertFalse(self.sync.fail)

    def assert_error(self):
        self.logger.info.assert_not_called()
        self.logger.warning.assert_not_called()
        self.logger.error.assert_called_once()
        self.assertTrue(self.sync.fail)

    def test_sync_team_member__not_in_team(self):
        self.github_team.has_in_members.return_value = False
        return_value = self.sync.sync_team_member(self.employee1, self.project1)
        self.talker.get_user.assert_called_once_with(self.employee1.github_username)
        self.github_team.add_membership.assert_called_once_with(self.github_user, role="member")
        self.assert_info()
        self.assertTrue(return_value)

    def test_sync_team_member__already_in_team(self):
        self.github_team.has_in_members.return_value = True
        return_value = self.sync.sync_team_member(self.employee1, self.project1)
        self.talker.get_user.assert_called_once_with(self.employee1.github_username)
        self.github_team.add_membership.assert_not_called()
        self.assert_no_log()
        self.assertFalse(return_value)

    def create_or_update_team__create(self, side_effect=None):
        self.mockSyncMembers()
        self.talker.create_team = MagicMock(return_value=MagicMock(id="25"))
        self.talker.create_team.side_effect = side_effect
        self.project1.github_team_id = None
        self.project1.save()
        self.sync.create_or_update_team(self.project1)
        self.talker.create_team.assert_called_once_with(self.project1)
        self.sync.update_team.assert_not_called()

    def test_create_or_update_team__create(self):
        self.create_or_update_team__create()
        self.assertEqual(self.project1.github_team_id, "25")
        self.assert_info()

    def test_create_or_update_team__create_exception(self):
        self.create_or_update_team__create(self.exception)
        self.assert_error()

    def create_or_update_team__update(self, side_effect=None):
        self.mockSyncMembers()
        self.sync.update_team.side_effect = side_effect
        self.sync.create_or_update_team(self.project1)
        self.talker.create_team.assert_not_called()
        self.sync.update_team.assert_called_once_with(self.project1)

    def test_create_or_update_team__update(self):
        self.create_or_update_team__update()
        self.assert_no_log()

    def test_create_or_update_team__update_exception(self):
        self.create_or_update_team__update(self.exception)
        self.assert_error()

    def create_or_update_team__team_members(self, side_effect=None):
        self.mockSyncMembers()
        self.sync.sync_team_member.side_effect = side_effect
        self.sync.create_or_update_team(self.project1)
        self.sync.sync_team_member.assert_called_once_with(self.employee1, self.project1)
        self.sync.update_team.assert_called_once_with(self.project1)
        self.talker.create_team.assert_not_called()

    def test_create_or_update_team__team_members(self):
        self.create_or_update_team__team_members()
        self.assert_no_log()

    def test_create_or_update_team__team_members_exception(self):
        self.create_or_update_team__team_members(self.exception)
        self.assert_error()

    def create_or_update_team__remove_users(self, side_effect=None):
        self.mockSyncMembers()
        self.sync.remove_users_not_in_team.side_effect = side_effect
        self.sync.create_or_update_team(self.project1)
        self.sync.sync_team_member(self.project1)
        self.sync.remove_users_not_in_team.assert_called_once_with(self.project1)
        self.sync.update_team.assert_called_once_with(self.project1)
        self.talker.create_team.assert_not_called()

    def test_create_or_update_team__remove_users(self):
        self.create_or_update_team__remove_users()
        self.assert_no_log()

    def test_create_or_update_team__remove_users_exception(self):
        self.create_or_update_team__remove_users(self.exception)
        self.assert_error()

    def remove_users_not_in_team(self, login, role, side_effect1=None, side_effect2=None):
        self.setUpUser(login, role)
        self.talker.remove_user.side_effect = side_effect1
        self.github_team.remove_membership.side_effect = side_effect2
        self.sync.remove_users_not_in_team(self.project1)

    def test_remove_users_not_in_team__employee(self):
        self.remove_users_not_in_team(self.employee1.github_username, "member")
        self.github_team.remove_membership.assert_not_called()
        self.talker.remove_user.assert_not_called()
        self.assertEquals(self.sync.users_removed, 0)
        self.assert_no_log()

    def test_remove_users_not_in_team__no_employee(self):
        self.remove_users_not_in_team("anunwanteduser", "member")
        self.github_team.remove_membership.assert_not_called()
        self.talker.remove_user.assert_called_once_with(self.github_user)
        self.assertEquals(self.sync.users_removed, 1)
        self.assert_info()

    def test_remove_users_not_in_team__owner(self):
        self.remove_users_not_in_team("anunwanteduser", "admin")
        self.github_team.remove_membership.assert_called_once_with(self.github_user)
        self.talker.remove_user.assert_not_called()
        self.assertEquals(self.sync.users_removed, 1)
        self.assert_info()

    def test_remove_users_not_in_team__exception_employee(self):
        self.remove_users_not_in_team("anunwanteduser", "member", self.exception, None)
        self.github_team.remove_membership.assert_not_called()
        self.talker.remove_user.assert_called_once_with(self.github_user)
        self.assertEquals(self.sync.users_removed, 0)
        self.assert_error()

    def test_remove_users_not_in_team__exception_owner(self):
        self.remove_users_not_in_team("anunwanteduser", "admin", None, self.exception)
        self.github_team.remove_membership.assert_called_once_with(self.github_user)
        self.talker.remove_user.assert_not_called()
        self.assertEquals(self.sync.users_removed, 0)
        self.assert_error()

    def test_remove_team__user_in_employees(self):
        self.setUpUser(self.employee1.github_username, "member")
        self.sync.remove_team(self.project1)

        self.talker.remove_user.assert_called_once_with(self.github_user)
        self.github_team.delete.assert_called_once_with()
        self.assertEqual(self.sync.users_removed, 1)
        self.assertEqual(self.logger.info.call_count, 2)
        self.logger.info.reset_mock()
        self.assert_no_log()

    def test_remove_team__user_in_employees__exception(self):
        self.setUpUser(self.employee1.github_username, "member")
        self.talker.remove_user.side_effect = self.exception
        self.sync.remove_team(self.project1)

        self.talker.remove_user.assert_called_once_with(self.github_user)
        self.github_team.delete.assert_called_once_with()
        self.assertEqual(self.sync.users_removed, 0)
        self.logger.info.assert_called_once()
        self.logger.info.reset_mock()
        self.assert_error()

    def test_remove_team__user_not_in_employees(self):
        self.setUpUser("thisuserisownerandshouldnotberemovedfromtheorganization", "admin")
        self.sync.remove_team(self.project1)

        self.talker.remove_userremove_from_members.assert_not_called()
        self.github_team.delete.assert_called_once_with()
        self.assertEqual(self.sync.users_removed, 0)
        self.assert_info()

    def test_remove_team__user_not_in_employees__exception(self):
        self.setUpUser("thisuserisownerandshouldnotberemovedfromtheorganization", "admin")
        self.github_team.delete.side_effect = self.exception
        self.sync.remove_team(self.project1)

        self.talker.remove_user.assert_not_called()
        self.github_team.delete.assert_called_once_with()
        self.assertEqual(self.sync.users_removed, 0)
        self.assert_error()

    def test_archive_repo__already_archived(self):
        self.github_repo.archived = True
        self.assertFalse(self.sync.archive_repo(self.repo1))
        self.talker.get_repo.assert_called_once_with(self.repo1.github_repo_id)
        self.github_repo.edit.assert_not_called()
        self.assertEqual(self.sync.repos_archived, 0)
        self.assert_no_log()

    def test_archive_repo__not_yet_archived(self):
        self.github_repo.archived = False
        self.assertTrue(self.sync.archive_repo(self.repo1))
        self.talker.get_repo.assert_called_once_with(self.repo1.github_repo_id)
        self.github_repo.edit.assert_called_once_with(archived=True)
        self.assertEqual(self.sync.repos_archived, 1)
        self.assert_info()

    def test_archive_project__on_github(self):
        self.mockSyncMembers()
        self.sync.archive_project(self.project1)
        self.sync.archive_repo.assert_not_called()
        self.sync.remove_team.assert_called_once_with(self.project1)
        self.assertIsNone(self.project1.github_team_id)
        self.assert_no_log()

    def test_archive_project__team_not_on_github(self):
        self.mockSyncMembers()
        self.project1.github_team_id = None
        self.project1.save()
        self.sync.archive_project(self.project1)
        self.sync.archive_repo.assert_not_called()
        self.sync.remove_team.assert_not_called()
        self.assertIsNone(self.project1.github_team_id)
        self.assert_warning()

    def test_archive_project__team_exception(self):
        self.mockSyncMembers()
        self.sync.remove_team.side_effect = self.exception
        self.sync.archive_project(self.project1)
        self.sync.archive_repo.assert_not_called()
        self.sync.remove_team.assert_called_once_with(self.project1)
        self.assert_error()

    def test_update_repo__incorrect_name(self):
        self.github_repo.name = "test-repo2"
        self.sync.update_repo(self.repo1)
        self.github_team.add_to_repos.assert_not_called()
        self.github_repo.edit.assert_called_once_with(name=self.repo1.name)
        self.github_team.set_repo_permission.assert_not_called()
        self.assert_info()

    def test_update_repo__incorrect_permissions(self):
        self.github_team.get_repo_permission.return_value = MagicMock(admin=False)
        self.sync.update_repo(self.repo1)
        self.github_team.add_to_repos.assert_not_called()
        self.github_repo.edit.assert_not_called()
        self.github_team.set_repo_permission.assert_called_once_with(self.github_repo, "admin")
        self.assert_info()

    def test_update_repo__incorrect_privacy(self):
        self.github_repo.private = False
        self.sync.update_repo(self.repo1)
        self.github_team.add_to_repos.assert_not_called()
        self.github_repo.edit.assert_called_once_with(private=self.repo1.private)
        self.github_team.set_repo_permission.assert_not_called()
        self.assert_info()

    def test_update_repo__not_in_repos(self):
        self.github_team.has_in_repos.return_value = False
        self.sync.update_repo(self.repo1)
        self.github_team.add_to_repos.assert_called_once_with(self.github_repo)
        self.github_repo.edit.assert_not_called()
        self.github_team.set_repo_permission.assert_not_called()
        self.assert_info()

    def test_update_repo__all_correct(self):
        self.sync.update_repo(self.repo1)
        self.github_team.add_to_repos.assert_not_called()
        self.github_repo.edit.assert_not_called()
        self.github_team.set_repo_permission.assert_not_called()
        self.assert_no_log()

    def create_or_update_repo__create(self, side_effect=None):
        self.mockSyncMembers()
        self.talker.create_repo = MagicMock(return_value=MagicMock(id=25))
        self.talker.create_repo.side_effect = side_effect
        self.repo1.github_repo_id = None
        self.repo1.save()
        self.sync.create_or_update_repos(self.project1)
        self.repo1.refresh_from_db()
        self.talker.create_repo.assert_called_once_with(self.repo1)
        self.sync.update_repo.assert_not_called()

    def test_create_or_update_repo__create(self):
        self.create_or_update_repo__create()
        self.assertEqual(self.repo1.github_repo_id, 25)
        self.assertEqual(self.sync.repos_created, 1)
        self.assert_info()

    def test_create_or_update_repo__create_exception(self):
        self.create_or_update_repo__create(self.exception)
        self.assert_error()

    def create_or_update_repo__update(self, side_effect=None):
        self.mockSyncMembers()
        self.sync.update_repo.side_effect = side_effect
        self.sync.create_or_update_repos(self.project1)
        self.talker.create_repo.assert_not_called()
        self.sync.update_repo.assert_called_once_with(self.repo1)
        self.assertEqual(self.sync.repos_created, 0)

    def test_create_or_update_repo__update(self):
        self.create_or_update_repo__update()
        self.assert_no_log()

    def test_create_or_update_repo__update_exception(self):
        self.create_or_update_repo__update(self.exception)
        self.assert_error()

    def test_update_team__all_correct(self):
        self.assertFalse(self.sync.update_team(self.project1))
        self.github_team.edit.assert_not_called()
        self.assert_no_log()

    def test_update_team__incorrect_description(self):
        self.github_team.description = "Wrong description"
        self.assertTrue(self.sync.update_team(self.project1))
        self.github_team.edit.assert_called_with(
            name=self.project1.name, description=self.project1.generate_team_description()
        )
        self.assert_info()

    def test_update_team__incorrect_name(self):
        self.github_team.name = "The wrong name"
        self.assertTrue(self.sync.update_team(self.project1))
        self.github_team.edit.assert_called_with(
            name=self.project1.name, description=self.project1.generate_team_description()
        )
        self.assert_info()

    def test_create_repo(self):
        self.talker.create_repo.return_value = "ThisShouldBeAPyGithubRepo"
        returned_repo = self.sync.create_repo(self.repo1)
        self.talker.create_repo.assert_called_once_with(self.repo1)
        self.assertEquals(returned_repo, "ThisShouldBeAPyGithubRepo")
        self.github_team.add_to_repos.assert_called_once_with(returned_repo)
        self.github_team.set_repo_permission.assert_called_once_with(returned_repo, "admin")

    def test_sync_project__not_archived(self):
        self.mockSyncMembers()
        self.repo2.is_archived = False
        self.repo2.save()
        self.repo1.is_archived = False
        self.repo1.save()
        self.sync.create_or_update_team = MagicMock()
        self.sync.create_or_update_repos = MagicMock()
        self.sync.archive_project = MagicMock()
        self.sync.sync_project(self.project1)
        self.sync.create_or_update_team.assert_called_once_with(self.project1)
        self.sync.create_or_update_repos.assert_called_once_with(self.project1)
        self.sync.archive_project.assert_not_called()
        self.sync.archive_repo.assert_not_called()

    def test_sync_project__one_archived(self):
        self.mockSyncMembers()
        self.repo2.is_archived = False
        self.repo2.save()
        self.repo1.is_archived = True
        self.repo1.save()
        self.sync.create_or_update_team = MagicMock()
        self.sync.create_or_update_repos = MagicMock()
        self.sync.archive_project = MagicMock()
        self.sync.sync_project(self.project1)
        self.sync.create_or_update_team.assert_called_once_with(self.project1)
        self.sync.create_or_update_repos.assert_called_once_with(self.project1)
        self.sync.archive_project.assert_not_called()
        self.sync.archive_repo.assert_called_once_with(self.repo1)

    def test_sync_project__all_archived(self):
        self.mockSyncMembers()
        self.repo2.is_archived = True
        self.repo2.save()
        self.repo1.is_archived = True
        self.repo1.save()
        self.sync.create_or_update_team = MagicMock()
        self.sync.create_or_update_repos = MagicMock()
        self.sync.archive_project = MagicMock()
        self.sync.sync_project(self.project1)
        self.sync.create_or_update_team.assert_not_called()
        self.sync.create_or_update_repos.assert_not_called()
        self.sync.archive_project.assert_called_once_with(self.project1)
        self.assertEqual(self.sync.archive_repo.call_count, 2)

    def test_archive_repos(self):
        self.mockSyncMembers()
        self.repo1.is_archived = True
        self.repo1.save()
        self.sync.archive_repos_marked_as_archived(self.project1)
        self.sync.archive_repo.assert_called_once_with(self.repo1)
        self.assert_no_log()

    def test_archive_repos__no_id(self):
        self.mockSyncMembers()
        self.repo1.is_archived = True
        self.repo1.github_repo_id = None
        self.repo1.save()
        self.sync.archive_repos_marked_as_archived(self.project1)
        self.sync.archive_repo.assert_not_called()
        self.assert_warning()

    def test_archive_repos__exception(self):
        self.mockSyncMembers()
        self.repo1.is_archived = True
        self.repo1.save()
        self.sync.archive_repo.side_effect = self.exception
        self.sync.archive_repos_marked_as_archived(self.project1)
        self.sync.archive_repo.assert_called_once_with(self.repo1)
        self.assert_error()

    def test_delete_teams_and_repos_to_be_deleted(self):
        self.sync.archive_repo = MagicMock()
        self.sync.remove_team = MagicMock()
        RepositoryToBeDeleted.delete = MagicMock()
        ProjectToBeDeleted.delete = MagicMock()
        self.sync.delete_teams_and_repos_to_be_deleted()
        for repo in RepositoryToBeDeleted.objects.all():
            self.sync.archive_repo.assert_any_call(repo)
        for team in ProjectToBeDeleted.objects.all():
            self.sync.remove_team.assert_any_call(team)
        self.repoToBeDeleted1.delete.assert_called()
        self.repoToBeDeleted2.delete.assert_called()
        self.projectToBeDeleted1.delete.assert_called()
        self.projectToBeDeleted2.delete.assert_called()

    def test_delete_teams_and_repos_to_be_deleted__exception_repo(self):
        self.sync.archive_repo = MagicMock(side_effect=GithubException(status=mock.Mock(status=500), data="abc"))
        self.sync.remove_team = MagicMock()
        self.sync.delete_teams_and_repos_to_be_deleted()
        self.logger.error.assert_called()

    def test_delete_teams_and_repos_to_be_deleted__exception_team(self):
        self.sync.archive_repo = MagicMock()
        self.sync.remove_team = MagicMock(side_effect=GithubException(status=mock.Mock(status=500), data="abc"))
        self.sync.delete_teams_and_repos_to_be_deleted()
        self.logger.error.assert_called()

    def test_delete_teams_and_repos_to_be_deleted__unknown_object_exception_team(self):
        self.sync.archive_repo = MagicMock()
        self.sync.remove_team = MagicMock(side_effect=UnknownObjectException(status=mock.Mock(status=404), data="abc"))
        self.sync.delete_teams_and_repos_to_be_deleted()
        self.logger.error.assert_called()

    def test_delete_teams_and_repos_to_be_deleted__unknown_object_exception_repo(self):
        self.sync.archive_repo = MagicMock(
            side_effect=UnknownObjectException(status=mock.Mock(status=404), data="abc")
        )
        self.sync.remove_team = MagicMock()
        self.sync.delete_teams_and_repos_to_be_deleted()
        self.logger.error.assert_called()

    def test_perform_sync(self):
        self.sync.sync_project = MagicMock()
        self.sync.delete_teams_and_repos_to_be_deleted = MagicMock()
        self.sync.perform_sync()
        self.sync.delete_teams_and_repos_to_be_deleted.assert_called_once()
        self.sync.sync_project.assert_called_once_with(self.project1)

    def test_perform_asynchronous_sync(self):
        thread_instance = MagicMock()
        thread_mock = MagicMock(return_value=thread_instance)
        with patch("threading.Thread", thread_mock):
            self.sync.perform_asynchronous_sync()
        thread_mock.assert_called_once_with(target=self.sync.perform_sync)
        thread_instance.start.assert_called_once()
