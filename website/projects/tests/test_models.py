from django.test import TestCase

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration


class EmployeeQueryTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Sets up one semester, two projects and three employees"""
        cls.semester = Semester.objects.create(year=2020, season=Semester.SPRING)
        cls.project1 = Project.objects.create(name="test1", semester=cls.semester)
        cls.project2 = Project.objects.create(name="test2", semester=cls.semester)
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

    def test_get_engineers(self):
        """Tests if get_engineers returns only engineers"""
        self.addEngineerToProject(self.employee1, self.project1)
        self.addEngineerToProject(self.employee2, self.project1)
        self.addManagerToProject(self.employee3, self.project1)

        self.assertIn(self.employee1, self.project1.get_engineers())
        self.assertIn(self.employee2, self.project1.get_engineers())
        self.assertNotIn(self.employee3, self.project1.get_engineers())

    def test_get_managers(self):
        """Tests if get_managers returns only managers"""
        self.addEngineerToProject(self.employee1, self.project1)
        self.addEngineerToProject(self.employee2, self.project1)
        self.addManagerToProject(self.employee3, self.project1)

        self.assertNotIn(self.employee1, self.project1.get_managers())
        self.assertNotIn(self.employee2, self.project1.get_managers())
        self.assertIn(self.employee3, self.project1.get_managers())
