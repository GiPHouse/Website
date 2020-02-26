from courses.models import Course, Semester

from django.test import TestCase

from projects.models import Project

from registrations.models import Employee, Registration


class GetEmployeesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        """Sets up one semester, two projects and three employees"""
        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.project1 = Project.objects.create(name="test1", semester=cls.semester)
        cls.project2 = Project.objects.create(name="test2", semester=cls.semester)
        cls.employee1 = Employee.objects.create(github_id=0, github_username="user1")
        cls.employee2 = Employee.objects.create(github_id=1, github_username="user2")
        cls.employee3 = Employee.objects.create(github_id=2, github_username="user3")

    @classmethod
    def addEmployeeToProject(cls, employee, project):
        """Creates a registration with employee as user """
        Registration.objects.create(
            user=employee,
            project=project,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.sdm(),
            preference1=project,
            semester=cls.semester,
        )

    def test_empty(self):
        """"Tests if get_employees returns an empty queryset if the project has no employees"""
        self.assertEqual(self.project1.get_employees().count(), 0)

    def test_non_empty(self):
        """"Tests if get_employees returns a queryset with all employees of a project
            and only the employees of that project"""
        self.addEmployeeToProject(self.employee1, self.project1)
        self.addEmployeeToProject(self.employee2, self.project1)
        self.addEmployeeToProject(self.employee3, self.project2)

        self.assertIn(self.employee1, self.project1.get_employees())
        self.assertIn(self.employee2, self.project1.get_employees())
        self.assertEqual(self.project1.get_employees().count(), 2)

        self.assertIn(self.employee3, self.project2.get_employees())
        self.assertEqual(self.project2.get_employees().count(), 1)
