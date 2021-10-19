import logging
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration
from registrations.team_assignment import TeamAssignmentGenerator

User: Employee = get_user_model()


class TeamAssignmentTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.sdm = Course.objects.sdm()
        cls.se = Course.objects.se()

        cls.user1 = User.objects.create_user(
            first_name="User1", last_name="Test1", github_id=1, github_username="user1"
        )
        cls.user2 = User.objects.create_user(
            first_name="User2", last_name="Test2", github_id=2, github_username="user2"
        )
        cls.user3 = User.objects.create_user(
            first_name="User3", last_name="Test3", github_id=3, github_username="user3"
        )
        cls.user4 = User.objects.create_user(
            first_name="User4", last_name="Test4", github_id=4, github_username="user4"
        )
        cls.user5 = User.objects.create_user(
            first_name="User5", last_name="Test5", github_id=5, github_username="user5"
        )
        cls.user6 = User.objects.create_user(
            first_name="User6", last_name="Test6", github_id=6, github_username="user6"
        )
        cls.user7 = User.objects.create_user(
            first_name="User7", last_name="Test7", github_id=7, github_username="user7"
        )
        cls.user8 = User.objects.create_user(
            first_name="User8", last_name="Test8", github_id=8, github_username="user8"
        )
        cls.user9 = User.objects.create_user(
            first_name="User9", last_name="Test9", github_id=9, github_username="user9"
        )

        cls.project1 = Project.objects.create(name="Project 1", semester=cls.semester)
        cls.project2 = Project.objects.create(name="Project 2", semester=cls.semester)
        cls.project3 = Project.objects.create(name="Project 3", semester=cls.semester)

        cls.reg1 = Registration.objects.create(
            user=cls.user1,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg2 = Registration.objects.create(
            user=cls.user2,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg3 = Registration.objects.create(
            user=cls.user3,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.sdm,
            is_international=False,
        )
        cls.reg4 = Registration.objects.create(
            user=cls.user4,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg5 = Registration.objects.create(
            user=cls.user5,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg6 = Registration.objects.create(
            user=cls.user6,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.sdm,
            is_international=False,
        )
        cls.reg7 = Registration.objects.create(
            user=cls.user7,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg8 = Registration.objects.create(
            user=cls.user8,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.se,
            is_international=False,
        )
        cls.reg9 = Registration.objects.create(
            user=cls.user9,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.sdm,
            is_international=False,
        )

    def setUp(self):
        logging.disable(logging.WARNING)
        for i in range(1, 10):
            self.__getattribute__(f"reg{i}").refresh_from_db()

    def tearDown(self) -> None:
        Project.objects.filter(semester=self.semester).delete()
        Registration.objects.filter(semester=self.semester).delete()

    def test_solve_csp__normal_no_partner_preferences_no_project_preference(self):
        self.assertIsNotNone(TeamAssignmentGenerator(Registration.objects.all()).generate_team_assignment())

    def test_solve_csp__normal_no_partner_preferences_with_project_preference(self):
        self.reg9.preference1 = self.project1
        self.reg9.preference2 = self.project2
        self.reg9.preference3 = self.project3
        self.reg9.save()
        self.reg8.preference1 = self.project1
        self.reg8.preference2 = self.project2
        self.reg8.preference3 = self.project3
        self.reg8.save()
        self.reg7.preference1 = self.project1
        self.reg7.preference2 = self.project3
        self.reg7.preference3 = self.project2
        self.reg7.save()
        self.reg6.preference1 = self.project3
        self.reg6.preference2 = self.project1
        self.reg6.preference3 = self.project2
        self.reg6.save()
        self.reg5.preference1 = self.project3
        self.reg5.preference2 = self.project1
        self.reg5.preference3 = self.project2
        self.reg5.save()
        self.reg4.preference1 = self.project3
        self.reg4.preference2 = self.project2
        self.reg4.preference3 = self.project1
        self.reg4.save()
        self.reg3.preference1 = self.project2
        self.reg3.preference2 = self.project3
        self.reg3.preference3 = self.project1
        self.reg3.save()
        self.reg2.preference1 = self.project2
        self.reg2.preference2 = self.project3
        self.reg2.preference3 = self.project1
        self.reg2.save()
        self.reg1.preference1 = self.project2
        self.reg1.preference2 = self.project1
        self.reg1.preference3 = self.project3
        self.reg1.save()
        expected_assignment = {
            self.reg1.pk: self.project2,
            self.reg2.pk: self.project2,
            self.reg3.pk: self.project2,
            self.reg4.pk: self.project3,
            self.reg5.pk: self.project3,
            self.reg6.pk: self.project3,
            self.reg7.pk: self.project1,
            self.reg8.pk: self.project1,
            self.reg9.pk: self.project1,
        }

        actual_assignment = TeamAssignmentGenerator(Registration.objects.all()).generate_team_assignment()

        self.assertDictEqual(expected_assignment, actual_assignment)

    def test_solve_csp__normal_with_partner_preferences_no_project_preference(self):
        self.reg9.partner_preference1 = str(self.user8)
        self.reg9.partner_preference2 = str(self.user7)
        self.reg9.partner_preference3 = None
        self.reg9.save()
        self.reg8.partner_preference1 = str(self.user9)
        self.reg8.partner_preference2 = str(self.user7)
        self.reg8.partner_preference3 = None
        self.reg8.save()
        self.reg7.partner_preference1 = str(self.user8)
        self.reg7.partner_preference2 = str(self.user9)
        self.reg7.partner_preference3 = None
        self.reg7.save()
        self.reg6.partner_preference1 = str(self.user4)
        self.reg6.partner_preference2 = str(self.user5)
        self.reg6.partner_preference3 = None
        self.reg6.save()
        self.reg5.partner_preference1 = str(self.user6)
        self.reg5.partner_preference2 = str(self.user4)
        self.reg5.partner_preference3 = None
        self.reg5.save()
        self.reg4.partner_preference1 = str(self.user5)
        self.reg4.partner_preference2 = str(self.user6)
        self.reg4.partner_preference3 = None
        self.reg4.save()
        self.reg3.partner_preference1 = str(self.user1)
        self.reg3.partner_preference2 = str(self.user2)
        self.reg3.partner_preference3 = None
        self.reg3.save()
        self.reg2.partner_preference1 = str(self.user3)
        self.reg2.partner_preference2 = str(self.user1)
        self.reg2.partner_preference3 = None
        self.reg2.save()
        self.reg1.partner_preference1 = str(self.user2)
        self.reg1.partner_preference2 = str(self.user3)
        self.reg1.partner_preference3 = None
        self.reg1.save()

        actual_assignment = TeamAssignmentGenerator(Registration.objects.all()).generate_team_assignment()

        group1 = actual_assignment[self.reg1.pk]
        group2 = actual_assignment[self.reg4.pk]
        group3 = actual_assignment[self.reg7.pk]
        expected_assignment = {
            self.reg1.pk: group1,
            self.reg2.pk: group1,
            self.reg3.pk: group1,
            self.reg4.pk: group2,
            self.reg5.pk: group2,
            self.reg6.pk: group2,
            self.reg7.pk: group3,
            self.reg8.pk: group3,
            self.reg9.pk: group3,
        }

        self.assertDictEqual(expected_assignment, actual_assignment)

    def test_solve_csp__mixed_programming_experience(self):
        self.reg1.experience = Registration.EXPERIENCE_BEGINNER
        self.reg1.save()
        self.reg2.experience = Registration.EXPERIENCE_BEGINNER
        self.reg2.save()
        self.reg4.experience = Registration.EXPERIENCE_INTERMEDIATE
        self.reg4.save()
        self.reg5.experience = Registration.EXPERIENCE_INTERMEDIATE
        self.reg5.save()
        self.reg7.experience = Registration.EXPERIENCE_ADVANCED
        self.reg7.save()
        self.reg8.experience = Registration.EXPERIENCE_ADVANCED
        self.reg8.save()

        actual_assignment = TeamAssignmentGenerator(Registration.objects.all()).generate_team_assignment()

        self.assertNotEqual(actual_assignment[self.reg1.pk], actual_assignment[self.reg2.pk])
        self.assertNotEqual(actual_assignment[self.reg4.pk], actual_assignment[self.reg5.pk])
        self.assertNotEqual(actual_assignment[self.reg7.pk], actual_assignment[self.reg8.pk])

    def test_solve_csp__too_many_internationals(self):
        Registration.objects.update(is_international=True)

        with patch("registrations.team_assignment.TeamAssignmentGenerator._add_constraints") as _:
            with patch(
                "registrations.team_assignment.TeamAssignmentGenerator._mixed_programming_experience_objective",
                return_value=0,
            ) as _:
                with patch("ortools.sat.python.cp_model.CpModel.Add") as mock_add:
                    assignment_generator = TeamAssignmentGenerator(Registration.objects.all())
                    assignment_generator._1_not_international_per_project_constraint()
                    self.assertIsNotNone(assignment_generator.generate_team_assignment())
                    mock_add.assert_not_called()

    def test_solve_csp__not_too_many_internationals(self):
        Registration.objects.update(is_international=False)

        with patch("registrations.team_assignment.TeamAssignmentGenerator._add_constraints") as _:
            with patch("ortools.sat.python.cp_model.CpModel.Add") as mock_add:
                assignment_generator = TeamAssignmentGenerator(Registration.objects.all())
                assignment_generator._1_not_international_per_project_constraint()
                self.assertIsNotNone(assignment_generator.generate_team_assignment())
                mock_add.assert_called()

    @patch("registrations.team_assignment.TeamAssignmentGenerator.generate_team_assignment", return_value=[])
    def test_solve_task_no_solution(self, generate_mock):
        logging.disable(logging.CRITICAL)
        assignment_generator = TeamAssignmentGenerator(Registration.objects.all())
        assignment_generator.execute_solve_task()
        generate_mock.assert_called_once()
        self.assertEqual(assignment_generator.task.completed, 1)
        self.assertTrue(assignment_generator.task.fail)

    @patch("registrations.team_assignment.TeamAssignmentGenerator.generate_team_assignment")
    def test_solve_task_solution(self, generate_mock):
        generate_mock.return_value = {self.reg1.pk: self.project1}
        assignment_generator = TeamAssignmentGenerator(Registration.objects.all())
        assignment_generator.execute_solve_task()
        generate_mock.assert_called_once()
        result = (
            '"First name","Last name","Student number","Course","Project name","Non Dutch",'
            '"Available during scheduled timeslot","Remarks","Programming experience",'
            '"At least one preference fulfilled","Has preferred project","Project preference 1",'
            '"Project preference 2","Project preference 3","In project with preferred students",'
            '"Student preference 1","Student preference 2","Student preference 3"\r\n'
            '"User2","Test2","","Software Engineering","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User4","Test4","","Software Engineering","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User5","Test5","","Software Engineering","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User7","Test7","","Software Engineering","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User8","Test8","","Software Engineering","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User3","Test3","","System Development Management","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User6","Test6","","System Development Management","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User9","Test9","","System Development Management","","","x","","1","x","1","","","","0","","",""\r\n'
            '"User1","Test1","","Software Engineering","Project 1","","x","","1","","","","","","0","","",""\r\n'
        )

        self.assertEqual(assignment_generator.task.data, result)
        self.assertEqual(assignment_generator.task.completed, 1)
        self.assertFalse(assignment_generator.task.fail)
