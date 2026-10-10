# import logging
from unittest.mock import MagicMock, patch

from django.contrib import messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Course, Semester

from projects.models import Project

from registrations.admin import UserAdminProjectFilter, UserAdminSemesterFilter
from registrations.models import Employee, Registration
from registrations.models.registration import (
    Question,
    QuestionChoice,
    Registrations,
    RegistrationSubmission,
    Answer,
    TextData,
)

User: Employee = get_user_model()


class RegistrationAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        Course.objects.create(name="Software Engineering")
        Course.objects.create(name="System Development Management")
        Course.objects.create(name="Software Development Entrepreneurship")

        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(
            github_id=0, github_username="super"
        )

        cls.course = Course.objects.sdm()

        cls.courseSE = Course.objects.se()

        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.semester.registration_start = timezone.now() - timezone.timedelta(
            days=30
        )
        cls.semester.registration_end = timezone.now() + timezone.timedelta(
            days=30
        )
        cls.semester.save()

        cls.project = Project.objects.create(
            name="GiPHouse1234",
            slug="giphouse1234",
            description="Test",
            semester=cls.semester,
        )
        cls.project2 = Project.objects.create(
            name="4321aProject",
            slug="4321aproject",
            description="Test",
            semester=cls.semester,
        )

        cls.manager = User.objects.create(
            github_id=1,
            github_username="manager",
            first_name="Man",
            last_name="Ager",
            student_number="s1234567",
        )

        cls.registration = Registration.objects.create(
            user=cls.manager,
            semester=cls.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=cls.project,
            partner_preference1="Partner name",
            course=cls.course,
            comments="comment",
            is_international=False,
        )
        cls.registration.add_project(cls.project)

        # Create corresponding RegistrationSubmission with projects
        cls.reg_submission_obj = Registrations.objects.create(
            title="Test", semester=cls.semester
        )
        cls.reg_submission = RegistrationSubmission.objects.create(
            registration=cls.reg_submission_obj,
            participant=cls.manager,
            course=cls.course,
        )
        cls.reg_submission.add_project(cls.project)

        cls.user = User.objects.create(
            github_id=2,
            github_username="lol",
            first_name="First",
            last_name="Last",
            student_number="s1234568",
        )

        cls.registration2 = Registration.objects.create(
            user=cls.user,
            semester=cls.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=cls.project,
            course=cls.course,
            is_international=False,
        )

        cls.reg_submission2 = RegistrationSubmission.objects.create(
            registration=cls.reg_submission_obj,
            participant=cls.user,
            course=cls.course,
        )

        cls.manager2 = User.objects.create(
            github_id=3,
            github_username="lmao",
            first_name="Mr",
            last_name="Bond",
            student_number="s007",
        )

        cls.registration3 = Registration.objects.create(
            user=cls.manager2,
            semester=cls.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=cls.project,
            course=cls.course,
            is_international=False,
        )
        cls.registration3.add_project(cls.project)
        cls.registration3.add_project(cls.project2)

        cls.reg_submission3 = RegistrationSubmission.objects.create(
            registration=cls.reg_submission_obj,
            participant=cls.manager2,
            course=cls.course,
        )
        cls.reg_submission3.add_project(cls.project)
        cls.reg_submission3.add_project(cls.project2)

        cls.userNoReg = User.objects.create(
            github_id=9,
            github_username="hahaha",
            first_name="No",
            last_name="Registration",
            student_number="s009",
        )

        cls.userNoPreference = User.objects.create(
            github_id=10,
            github_username="dontmind",
            first_name="No",
            last_name="Preference",
            student_number="s010",
        )

        cls.registration4 = Registration.objects.create(
            user=cls.userNoPreference,
            semester=cls.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            course=cls.course,
            is_international=False,
        )

        cls.message = {
            "first_name": "Bob",
            "last_name": "Bobby",
            "email": "",
            "student_number": "s0000000",
            "date_joined_0": "2000-12-01",
            "date_joined_1": "12:00:00",
            "initial-date_joined_0": "2000-12-01",
            "initial-date_joined_1": "12:00:00",
            "github_id": 4,
            "github_username": "bob",
            "comments": "",
            "registrationsubmission_set-TOTAL_FORMS": 0,
            "registrationsubmission_set-INITIAL_FORMS": 0,
            "registrationsubmission_set-MIN_NUM_FORMS": 0,
            "registrationsubmission_set-MAX_NUM_FORMS": 1000,
            "_save": "Save",
        }

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def test_get_changelist(self):
        response = self.client.get(
            reverse("admin:registrations_employee_changelist"), follow=True
        )
        self.assertEqual(response.status_code, 200)

    def test_get_form(self):
        response = self.client.get(
            reverse(
                "admin:registrations_employee_change", args=[self.manager.id]
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_form_save(self):
        response = self.client.post(
            reverse("admin:registrations_employee_add"),
            self.message,
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(student_number="s0000000"))

    def test_student_change_list_without_registration(self):
        response = self.client.get(
            reverse(
                "admin:registrations_employee_change", args=[self.user.pk]
            ),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_user_changelist_semesterfilter(self):
        response = self.client.get(
            reverse("admin:registrations_employee_changelist"),
            data={UserAdminSemesterFilter.parameter_name: self.semester.id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_user_changelist_projectfilter(self):
        response = self.client.get(
            reverse("admin:registrations_employee_changelist"),
            data={
                f"{UserAdminProjectFilter.field_name}__{UserAdminProjectFilter.field_pk}__exact": self.project.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_student_number_csv_export(self):
        response = self.client.post(
            reverse("admin:registrations_employee_changelist"),
            {
                ACTION_CHECKBOX_NAME: [self.user.pk],
                "action": "export_student_numbers",
                "index": 0,
            },
        )

        self.assertContains(
            response, '"First name","Last name","Student number"'
        )
        self.assertContains(
            response,
            f'"{self.user.first_name}","{self.user.last_name}","{self.user.student_number}"',
        )
        self.assertEqual(response.status_code, 200)

    def test_registration_csv_export(self):
        # Create a Registrations object (the registration form)
        registration_form = Registrations.objects.create(
            title="Test Registration Form",
            semester=self.semester,
        )

        # Create questions with appropriate labels
        question_labels = {
            "projects": Question.PROJECTS,
            "partners": Question.PARTNERS,
            "devexp": Question.DEVEXP,
            "gitexp": Question.GITEXP,
            "scrumexp": Question.SCRUMEXP,
            "management": Question.MANAGEMENT,
            "nondutch": Question.NONDUTCH,
            "timeslots": Question.TIMESLOTS,
            "nonda": Question.NONDA,
            "comments": Question.COMMENTS,
        }

        questions = {}
        for key, label in question_labels.items():
            questions[key] = Question.objects.create(
                registration=registration_form,
                question=f"Question for {key}",
                question_type=Question.TEXT,
                label=label,
            )

        # Create timeslot choices
        timeslot_values = [
            f"available during scheduled timeslot {i}" for i in range(1, 11)
        ]
        timeslot_question = Question.objects.create(
            registration=registration_form,
            question="Which timeslots are you available?",
            question_type=Question.MULTI,
            label=Question.TIMESLOTS,
        )
        for value in timeslot_values:
            QuestionChoice.objects.create(
                question=timeslot_question, value=value
            )

        # Create a RegistrationSubmission for the manager
        submission = RegistrationSubmission.objects.create(
            registration=registration_form,
            participant=self.manager,
            course=self.registration.course,
        )

        # Create Answer objects for each question
        answers_data = {
            "projects": f'"{self.registration.preference1}"',
            "partners": f'"{self.registration.partner_preference1}"',
            "devexp": f'"{self.registration.dev_experience}"',
            "gitexp": f'"{self.registration.dev_experience}"',
            "scrumexp": f'"{self.registration.dev_experience}"',
            "management": "False",
            "nondutch": f'"{self.registration.is_international}"',
            "timeslots": "available during scheduled timeslot 1, available during scheduled timeslot 2",
            "nonda": "False",
            "comments": f'"{self.registration.comments}"',
        }

        for key, value in answers_data.items():
            answer = Answer.objects.create(
                question=questions[key],
                submission=submission,
            )
            TextData.objects.create(answer=answer, value=value)

        # Mock the current_registration to return our test registration form
        with patch(
            "registrations.admin.Registrations.objects.current_registration"
        ) as mock_current_reg:
            mock_current_reg.return_value = registration_form

            response = self.client.post(
                reverse("admin:registrations_employee_changelist"),
                {
                    ACTION_CHECKBOX_NAME: [self.manager.pk],
                    "action": "export_registrations",
                    "index": 0,
                },
            )

            # Check response contains expected headers
            self.assertContains(
                response,
                '"First name","Last name","Student number","GitHub username","Course","project preferences","partner preferences","Dev Experience","Git Experience","Scrum Experience","Management Interest","Non-dutch","Availablility timeslots","Has problems with signing an NDA","Registration Comments"',
            )

            # Check response contains manager's data
            self.assertContains(response, f'"{self.manager.first_name}"')
            self.assertContains(response, f'"{self.manager.last_name}"')
            self.assertContains(response, f'"{self.manager.student_number}"')
            self.assertContains(response, f'"{self.manager.github_username}"')

    def test_unassign_project(self):
        response = self.client.post(
            reverse("admin:registrations_employee_changelist"),
            {
                ACTION_CHECKBOX_NAME: [
                    self.manager.pk,
                    self.user.pk,
                    self.manager2.pk,
                ],
                "action": "unassign_from_project",
                "index": 0,
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.reg_submission.refresh_from_db()
        self.reg_submission2.refresh_from_db()
        self.reg_submission3.refresh_from_db()
        self.assertFalse(self.reg_submission.has_projects())
        self.assertFalse(self.reg_submission2.has_projects())
        self.assertFalse(self.reg_submission3.has_projects())

    def test_import_csv__get(self):
        response = self.client.get(reverse("admin:import"), follow=True)
        self.assertEqual(response.status_code, 200)

    @patch("registrations.admin.ImportAssignmentAdminView.handle_csv")
    def test_import_csv__post(self, mock_handle_csv):
        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", b"123456,test,abcdef", content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        mock_handle_csv.assert_called_once()

    @patch("registrations.admin.ImportAssignmentAdminView.handle_csv")
    def test_import_csv__post_no_csv_file(self, mock_handle_csv):
        messages.error = MagicMock()
        test_csv_file = SimpleUploadedFile(
            "csv_file.png", b"123456,test,abcdef", content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        messages.error.assert_called_once()
        mock_handle_csv.assert_not_called()

    @patch("registrations.admin.ImportAssignmentAdminView.handle_csv")
    def test_import_csv__post_file_too_big(self, mock_handle_csv):
        messages.error = MagicMock()
        file_content = 20000000 * b"test"
        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        messages.error.assert_called_once()
        mock_handle_csv.assert_not_called()

    @patch(
        "registrations.admin.ImportAssignmentAdminView.handle_csv",
        **{"return_value.raiseError.side_effect": ValueError()},
    )
    def test_import_csv__post_file_error_handling(self, mock_handle_csv):
        messages.error = MagicMock()
        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", b"123456,test,abcdef", content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        mock_handle_csv.assert_called_once()
        messages.error.assert_called_once()

    def test_handle_csv(self):
        file_content = (
            b"First name, Last name, Student number, Course, Project name\nPiet, Janssen, s1234569, "
            b"System Development Management, GiPHouse1234"
        )
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s1234569",
        )
        # Create Registration object for reference
        registration = Registration.objects.create(  # noqa: F841, REMOVE THIS COMMENT WHEN THIS OBJECT IS ACTUALLY USED.
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )

        # Create RegistrationSubmission object (which is what handle_csv works with)
        reg_submission = RegistrationSubmission.objects.create(
            registration=self.reg_submission_obj,
            participant=user,
            course=self.course,
        )

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        reg_submission.refresh_from_db()
        self.assertIn(self.project, reg_submission.get_projects())
        self.assertEqual(response.status_code, 200)

    def test_handle_csv__already_assigned(self):
        file_content = (
            b"First name, Last name, Student number, Course, Project name\nPiet, Janssen, s1234569, "
            b"System Development Management, GiPHouse1234"
        )
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s1234569",
        )
        registration = Registration.objects.create(
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )
        registration.add_project(self.project2)

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        registration.refresh_from_db()
        self.assertIn(self.project2, registration.get_projects())
        self.assertEqual(response.status_code, 200)

    def test_handle_csv__invalid_header(self):
        file_content = b"Piet, Janssen, s1234569, System Development Management, GiPHouse1234"
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s1234569",
        )
        registration = Registration.objects.create(
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        registration.refresh_from_db()
        self.assertFalse(registration.has_projects())
        self.assertEqual(response.status_code, 200)

    def test_handle_csv__nonexistent_project(self):
        file_content = (
            b"First name, Last name, Student number, Course, Project name\nPiet, Janssen, s1234569, "
            b"System Development Management, NonExistingProject"
        )
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s1234569",
        )
        registration = Registration.objects.create(
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        registration.refresh_from_db()
        self.assertFalse(registration.has_projects())
        self.assertEqual(response.status_code, 200)

    def test_handle_csv__no_project(self):
        file_content = (
            b"First name, Last name, Student number, Course, Project name\nPiet, Janssen, s1234569, "
            b"System Development Management,"
        )
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s1234569",
        )
        registration = Registration.objects.create(
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        registration.refresh_from_db()
        self.assertFalse(registration.has_projects())
        self.assertEqual(response.status_code, 200)

    def test_handle_csv__nonexistent_user(self):
        file_content = (
            b"First name, Last name, Student number, Course, Project name\nPiet, Janssen, s1234569, "
            b"System Development Management, GiPHouse1234"
        )
        user = User.objects.create(
            github_id=1234567,
            github_username="abcdefghij",
            first_name="Piet",
            last_name="Janssen",
            student_number="s0000000",
        )
        registration = Registration.objects.create(
            user=user,
            semester=self.semester,
            dev_experience=Registration.EXPERIENCE_BEGINNER,
            preference1=self.project,
            course=self.course,
            is_international=False,
        )

        test_csv_file = SimpleUploadedFile(
            "csv_file.csv", file_content, content_type="text/csv"
        )
        response = self.client.post(
            reverse("admin:import"),
            {"csv_file": test_csv_file, "semester": self.semester.pk},
            follow=True,
        )
        registration.refresh_from_db()
        self.assertFalse(registration.has_projects())
        self.assertEqual(response.status_code, 200)

    def test_convert_timeslots(self):
        from registrations.admin import UserAdmin
        from registrations.models.registration import (
            Question,
            QuestionChoice,
            Registrations,
        )

        # Set up mock registration with timeslot choices in the database
        mock_registration = Registrations.objects.create(
            title="Test Registration",
            semester=self.semester,
        )

        # Create a question with label "timeslots"
        timeslot_question = Question.objects.create(
            registration=mock_registration,
            question="Which timeslots are you available?",
            question_type=Question.MULTI,
            label=Question.TIMESLOTS,
        )

        # Create 10 timeslot choices
        timeslot_choices = []
        for i in range(1, 11):
            choice = QuestionChoice.objects.create(
                question=timeslot_question,
                value=f"available during scheduled timeslot {i}",
            )
            timeslot_choices.append(choice)

        # Mock the current_registration to return our test registration
        with patch(
            "registrations.admin.Registrations.objects.current_registration"
        ) as mock_current_reg:
            mock_current_reg.return_value = mock_registration

            user_admin = UserAdmin(User, None)

            # Test with multiple timeslots
            self.assertEqual(
                user_admin.convert_timeslots(
                    "available during scheduled timeslot 1, available during scheduled timeslot 2"
                ),
                [
                    True,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            )

            # Test with single timeslot
            self.assertEqual(
                user_admin.convert_timeslots(
                    "available during scheduled timeslot 2"
                ),
                [
                    False,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            )

            # Test with timeslot 5
            self.assertEqual(
                user_admin.convert_timeslots(
                    "available during scheduled timeslot 5"
                ),
                [
                    False,
                    False,
                    False,
                    False,
                    True,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            )

            # Test with timeslot 10
            self.assertEqual(
                user_admin.convert_timeslots(
                    "available during scheduled timeslot 10"
                ),
                [
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    True,
                ],
            )

            # Test with multiple non-consecutive timeslots
            self.assertEqual(
                user_admin.convert_timeslots(
                    "available during scheduled timeslot 1, available during scheduled timeslot 5, available during scheduled timeslot 10"
                ),
                [
                    True,
                    False,
                    False,
                    False,
                    True,
                    False,
                    False,
                    False,
                    False,
                    True,
                ],
            )

            # Test with empty string
            self.assertEqual(
                user_admin.convert_timeslots(""),
                [
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                    False,
                ],
            )
