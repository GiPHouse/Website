from unittest.mock import MagicMock

from django.test import TestCase

from courses.models import Course, Semester

from projects import githubsync
from projects.models import AWSPolicy, Project, ProjectToBeDeleted, Repository, RepositoryToBeDeleted

from registrations.models import Employee, Registration


class EmployeeQueryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Sets up one semester, four projects and three employees"""
        cls.semester = Semester.objects.create(year=2020, season=Semester.SPRING)
        cls.project1 = Project.objects.create(name="test1", slug="test1", semester=cls.semester)
        cls.project2 = Project.objects.create(name="test2", slug="test2", semester=cls.semester)
        cls.project3 = Project.objects.create(name="test3", slug="test3", semester=cls.semester)
        cls.project4 = Project.objects.create(
            name="test4", slug="test4", semester=cls.semester, github_team_id=12345678
        )
        cls.repo1 = Repository.objects.create(name="testrepo1", project=cls.project3)
        cls.repo2 = Repository.objects.create(name="testrepo2", project=cls.project3, github_repo_id=87654321)
        cls.repo3 = Repository.objects.create(name="testrepo3", project=cls.project2)
        cls.employee1 = Employee.objects.create(github_id=0, github_username="user1")
        cls.employee2 = Employee.objects.create(github_id=1, github_username="user2")
        cls.employee3 = Employee.objects.create(github_id=2, github_username="user3")

    @classmethod
    def addManagerToProject(cls, employee, project):
        """Adds employee to a project as a manager"""
        Registration.objects.create(
            user=employee,
            project=project,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.sdm(),
            preference1=project,
            semester=cls.semester,
        )

    @classmethod
    def addEngineerToProject(cls, employee, project):
        """Adds employee to a project as an engineer"""
        Registration.objects.create(
            user=employee,
            project=project,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.sde(),
            preference1=project,
            semester=cls.semester,
        )

    def test_generate_team_description(self):
        """Tests a correct team description for a project."""
        self.assertEquals(
            self.project1.generate_team_description(),
            "Team for the GiPHouse project 'test1' for the 'Spring 2020' semester.",
        )

    def test_empty(self):
        """Tests if get_employees returns an empty queryset if the project has no employees"""
        self.assertEqual(self.project1.get_employees().count(), 0)

    def test_non_empty(self):
        """Tests if get_employees returns a queryset with all employees of a project
        and only the employees of that project"""
        self.addEngineerToProject(self.employee1, self.project1)
        self.addEngineerToProject(self.employee2, self.project1)
        self.addEngineerToProject(self.employee3, self.project2)

        self.assertIn(self.employee1, self.project1.get_employees())
        self.assertIn(self.employee2, self.project1.get_employees())
        self.assertEqual(self.project1.get_employees().count(), 2)

        self.assertIn(self.employee3, self.project2.get_employees())
        self.assertEqual(self.project2.get_employees().count(), 1)

    def test_delete_project(self):
        """Test if deleted projects are also added to delete-list and its repositories are deleted too."""
        githubsync.talker.remove_team = MagicMock()

        self.project3.delete()
        self.assertEqual(ProjectToBeDeleted.objects.all().count(), 0)
        self.assertTrue(RepositoryToBeDeleted.objects.get(github_repo_id=87654321))
        self.assertEqual(len(Repository.objects.filter(name="testrepo1")), 0)
        self.assertEqual(len(Repository.objects.filter(name="testrepo2")), 0)

        self.project4.delete()
        self.assertTrue(ProjectToBeDeleted.objects.get(github_team_id=12345678))

    def test_delete_repository(self):
        """Test if deleted repos are added to delete-list."""
        githubsync.talker.archive_repo = MagicMock()

        self.repo1.delete()
        self.assertEqual(RepositoryToBeDeleted.objects.all().count(), 0)

        self.repo2.delete()
        self.assertTrue(RepositoryToBeDeleted.objects.get(github_repo_id=87654321))

    def test_is_archived(self):
        self.assertEqual(self.project2.is_archived, Repository.Archived.NOT_ARCHIVED)

    def test_is_archived__no_repos(self):
        self.assertEqual(self.project1.is_archived, Repository.Archived.CONFIRMED)

    def test_number_of_repos(self):
        project = Project.objects.create(name="testproject", semester=self.semester)
        self.assertEqual(project.number_of_repos, 0)
        Repository.objects.create(name="testrepository1", project=project)
        Repository.objects.create(name="testrepository2", project=project)
        self.assertEqual(project.number_of_repos, 2)


class AWSPolicySaveTest(TestCase):
    def test_save_method_with_existing_current_policy(self):
        existing_policy = AWSPolicy.objects.create(is_current_policy=True)
        new_policy = AWSPolicy(is_current_policy=True)
        new_policy.save()
        existing_policy.refresh_from_db()
        self.assertFalse(existing_policy.is_current_policy)
        self.assertTrue(new_policy.is_current_policy)

    def test_save_method_without_existing_current_policy_false(self):
        policy = AWSPolicy(is_current_policy=False)
        policy.save()
        self.assertFalse(policy.is_current_policy)

    def test_save_method_without_existing_current_policy_true(self):
        policy = AWSPolicy(is_current_policy=True)
        policy.save()
        self.assertTrue(policy.is_current_policy)
