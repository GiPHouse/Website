from unittest.mock import MagicMock

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.db import models

from courses.models import Course, Semester

from projects import githubsync
from projects.models import (
    Project,
    ProjectToBeDeleted,
    Repository,
    RepositoryToBeDeleted,
    Client,
    ExistingRepository,
)

from registrations.models import Employee, Registration

from django.db.utils import IntegrityError


class ExistingRepositoryTests(TestCase):
    def test_clean_fails_with_id_no_name(self):
        repo = ExistingRepository(
            github_repo_id=12345,
            name="",
        )

        with self.assertRaises(ValidationError):
            repo.full_clean()

    def test_valid_input_no_exception(self):
        repo = ExistingRepository(
            github_repo_id=12345,
            name="test-repo",
        )

        repo.full_clean()


class EmployeeQueryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Sets up one semester, four projects and three employees"""
        Course.objects.create(name="Software Engineering")
        Course.objects.create(name="System Development Management")
        Course.objects.create(name="Software Development Entrepreneurship")

        cls.semester = Semester.objects.create(
            year=2020, season=Semester.SPRING
        )
        cls.project1 = Project.objects.create(
            name="test1", slug="test1", semester=cls.semester
        )
        cls.project2 = Project.objects.create(
            name="test2", slug="test2", semester=cls.semester
        )
        cls.project3 = Project.objects.create(
            name="test3", slug="test3", semester=cls.semester
        )
        cls.project4 = Project.objects.create(
            name="test4",
            slug="test4",
            semester=cls.semester,
            github_team_id=12345678,
        )
        cls.repo1 = Repository.objects.create(
            name="testrepo1", project=cls.project3
        )
        cls.repo2 = Repository.objects.create(
            name="testrepo2", project=cls.project3, github_repo_id=87654321
        )
        cls.repo3 = Repository.objects.create(
            name="testrepo3", project=cls.project2
        )
        cls.employee1 = Employee.objects.create(
            github_id=0, github_username="user1"
        )
        cls.employee2 = Employee.objects.create(
            github_id=1, github_username="user2"
        )
        cls.employee3 = Employee.objects.create(
            github_id=2, github_username="user3"
        )

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
        reg = Registration.objects.create(
            user=employee,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.sde(),
            preference1=project,
            semester=cls.semester,
        )
        reg.add_project(project)

    def test_client_model_str_method(self):
        client_name = "free labor"
        client = Client.objects.create(name=client_name)

        self.assertEqual(str(client), f"{client_name}")

    def test_generate_team_description(self):
        """Tests a correct team description for a project."""
        self.assertEqual(
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
        self.assertTrue(
            RepositoryToBeDeleted.objects.get(github_repo_id=87654321)
        )
        self.assertEqual(len(Repository.objects.filter(name="testrepo1")), 0)
        self.assertEqual(len(Repository.objects.filter(name="testrepo2")), 0)

        self.project4.delete()
        self.assertTrue(
            ProjectToBeDeleted.objects.get(github_team_id=12345678)
        )
        proj_to_be_del = ProjectToBeDeleted.objects.get(
            github_team_id=12345678
        )

        # the implemented __str__ method should be different from the __str__ function in the
        # parent class (Model)
        self.assertNotEqual(
            str(proj_to_be_del), models.Model.__str__(proj_to_be_del)
        )
        self.assertIs(type(str(proj_to_be_del)), str)

    def test_delete_repository(self):
        """Test if deleted repos are added to delete-list."""
        githubsync.talker.archive_repo = MagicMock()

        self.repo1.delete()
        self.assertEqual(RepositoryToBeDeleted.objects.all().count(), 0)

        self.repo2.delete()
        self.assertTrue(
            RepositoryToBeDeleted.objects.get(github_repo_id=87654321)
        )
        repo_to_be_del = RepositoryToBeDeleted.objects.get(
            github_repo_id=87654321
        )

        # the implemented __str__ method should be different from the __str__ function in the
        # parent class (Model)
        self.assertNotEqual(
            str(repo_to_be_del), models.Model.__str__(repo_to_be_del)
        )
        self.assertIs(type(str(repo_to_be_del)), str)

    def test_is_archived(self):
        self.assertEqual(
            self.project2.is_archived, Repository.Archived.NOT_ARCHIVED
        )

    def test_is_archived__no_repos(self):
        self.assertEqual(
            self.project1.is_archived, Repository.Archived.CONFIRMED
        )

    def test_number_of_repos(self):
        project = Project.objects.create(
            name="testproject", semester=self.semester
        )
        self.assertEqual(project.number_of_repos, 0)
        Repository.objects.create(name="testrepository1", project=project)
        Repository.objects.create(name="testrepository2", project=project)
        self.assertEqual(project.number_of_repos, 2)

    def test_slug_name_already_exists(self):
        project1 = Project.objects.create(
            name="project1", slug="project-2020", semester=self.semester
        )
        project1.save()
        try:
            project2 = Project.objects.create(
                name="project2", slug="project-2020", semester=self.semester
            )
            project2.save()
            self.fail(
                "test_slug_name_already_exists FAILED: TWO PROJECTS WITH SAME SLUG"
            )
        except IntegrityError:
            pass

    def test_repo_name_already_exists(self):
        repo1 = Repository.objects.create(
            name="project1",
        )
        repo1.save()
        try:
            repo2 = Repository.objects.create(
                name="project1",
            )
            repo2.save()
            self.fail(
                "test_repo_name_already_exists FAILED: TWO REPOS WITH SAME NAME"
            )
        except IntegrityError:
            pass
