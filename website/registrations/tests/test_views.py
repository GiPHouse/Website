from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone
from django.utils.text import slugify

from courses.models import Course, Semester

from projects.models import Project

from registrations.admin import RegistrationsAdmin
from registrations.models import (
    Employee,
    Registrations,
    Question,
    QuestionChoice,
    RegistrationSubmission,
)
from registrations.utils.sample_registration_form import SampleRegistrationForm

User: Employee = get_user_model()


class RedirectTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_base_url_redirects_to_step_1(self):
        response = self.client.get("/register/")

        self.assertRedirects(
            response,
            reverse("registrations:step1"),
            fetch_redirect_response=False,
        )


class Step1Test(TestCase):
    @classmethod
    def setUpTestData(cls):

        cls.test_user = User.objects.create_user(github_id=0)
        cls.test_user.backend = ""

    def setUp(self):
        self.client = Client()

    def test_step1(self):
        semester = Semester.objects.get_or_create_current_semester()
        semester.registration_start = timezone.now()
        semester.registration_end = timezone.now() + timezone.timedelta(days=1)
        semester.save()

        response = self.client.get("/register/step1")

        self.assertEqual(response.status_code, 200)

    def test_step1_authenticated(self):
        semester = Semester.objects.get_or_create_current_semester()
        semester.registration_start = timezone.now()
        semester.registration_end = timezone.now() + timezone.timedelta(days=1)
        semester.save()

        self.client.force_login(self.test_user)

        response = self.client.get("/register/step1")
        self.assertFalse(response.context["user"].is_authenticated)

    def test_step1_no_semester(self):
        """Uncomment a branch of the dispatch() method of
        the Step1View Class for this test to pass."""

        response = self.client.get("/register/step1", follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Registrations are currently not open")

    def test_step1_semester_without_registrations(self):
        """Uncomment a branch of the dispatch() method of
        the Step1View Class for this test to pass."""

        Semester.objects.get_or_create_current_semester()

        response = self.client.get("/register/step1", follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Registrations are currently not open")

    def test_step1_current_semester_closed_registration(self):
        """Uncomment a branch of the dispatch() method of
        the Step1View Class for this test to pass."""

        semester = Semester.objects.get_or_create_current_semester()
        semester.registration_start = timezone.now() - timezone.timedelta(
            days=2
        )
        semester.registration_end = timezone.now() - timezone.timedelta(days=1)
        semester.save()

        response = self.client.get("/register/step1", follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Registrations are currently not open")

    def test_step1_old_semester_open_registration(self):
        Semester.objects.create(
            year=2017,
            season=Semester.SPRING,
            registration_start=timezone.now(),
            registration_end=timezone.now() + timezone.timedelta(days=1),
        )

        response = self.client.get("/register/step1", follow=True)

        self.assertEqual(response.status_code, 200)


class Step2Test(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create courses for the registration to offer as a choice
        cls.course = Course.objects.se()

        cls.sem = Semester.objects.get_or_create_current_semester()
        # ..and projects
        cls.project_preference1 = "Project A"
        cls.project_preference2 = "Project B"
        cls.project_preference3 = "Project C"

        Project.objects.create(
            name=cls.project_preference1,
            slug=slugify(cls.project_preference1),
            semester=cls.sem,
        )
        Project.objects.create(
            name=cls.project_preference2,
            slug=slugify(cls.project_preference2),
            semester=cls.sem,
        )
        Project.objects.create(
            name=cls.project_preference3,
            slug=slugify(cls.project_preference3),
            semester=cls.sem,
        )

        # create sample registration
        site = AdminSite()
        admin = RegistrationsAdmin(Registrations, site)
        # the request parameter is not used inside
        # the function, so None should work
        admin.create_sample_registration(None)

        cls.q_ids_start = Question.objects.all().first().pk
        sample_reg = SampleRegistrationForm()

        cls.devexp_question_id = (
            Question.objects.filter(question=sample_reg.devexp[0]).first().pk
        )

        timeslot_q_id = (
            Question.objects.filter(question=sample_reg.timeslots[0])
            .first()
            .pk
        )
        cls.availability_ids_start = (
            QuestionChoice.objects.filter(
                question_id=timeslot_q_id,
            )
            .first()
            .id
        )

        # Fields set by Step1
        cls.github_username = "test"
        cls.github_id = 1

        # Fields of the sample_reg form
        cls.first_name = "FirstTest"
        cls.last_name = "LastTest"
        cls.email = "test@test.com"
        cls.student_number = "s1234567"

        # choose any of the options, say, the first one
        cls.devexp = sample_reg.devexp[2][0]
        cls.git_experience = sample_reg.gitexp[2][2]
        cls.scrum_experience = sample_reg.scrumexp[2][0]

        cls.project_partner_preference1 = "Piet Janssen"
        cls.project_partner_preference2 = "FirstTest LastTest"
        cls.project_partner_preference3 = "Einstein"

        cls.available_during_scheduled_timeslots = [1, 2, 3, 10]

        cls.management_interest = sample_reg.management[2][0]
        cls.non_dutch = sample_reg.nondutch[2][0]
        cls.problem_with_NDA = sample_reg.nonda[2][0]

    def setUp(self):
        self.client = Client()

        self.session = self.client.session
        self.session["github_id"] = self.github_id
        self.session["github_username"] = self.github_username
        self.session["github_email"] = self.email
        self.session["github_name"] = f"{self.first_name} {self.last_name}"

        self.session.save()

        # All questions must be answered;
        # This is a sample payload, the values are based on
        # the human-readable attributes defined above
        self.form_data_filled = {
            f"question_{self.q_ids_start}_first_name": self.first_name,
            f"question_{self.q_ids_start + 1}_last_name": self.last_name,
            f"question_{self.q_ids_start + 2}_email": self.email,
            f"question_{self.q_ids_start + 3}_student_number": self.student_number,
            f"question_{self.q_ids_start + 4}_course": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 4,
                value=self.course,  # because it's a dropdown
            )
            .first()
            .pk,
            # Depends on the total number; we created 3, so 3 fields respectively.
            f"question_{self.q_ids_start + 5}_0": "",
            f"question_{self.q_ids_start + 5}_1": "",
            f"question_{self.q_ids_start + 5}_2": "",
            # Three partner preferences
            f"question_{self.q_ids_start + 6}_0": self.project_partner_preference1,  # TEXTLIST
            f"question_{self.q_ids_start + 6}_1": self.project_partner_preference2,
            f"question_{self.q_ids_start + 6}_2": self.project_partner_preference3,
            f"question_{self.q_ids_start + 7}": QuestionChoice.objects.filter(
                question_id=self.devexp_question_id,
                value=self.devexp,  # CHOICE
            )
            .first()
            .pk,
            f"question_{self.q_ids_start + 8}": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 8,
                value=self.git_experience,
            )
            .first()
            .pk,
            f"question_{self.q_ids_start + 9}": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 9,
                value=self.scrum_experience,
            )
            .first()
            .pk,
            f"question_{self.q_ids_start + 10}": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 10,
                value=self.management_interest,  # CHOICE
            )
            .first()
            .pk,
            f"question_{self.q_ids_start + 11}": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 11,
                value=self.non_dutch,  # CHOICE
            )
            .first()
            .pk,
            f"question_{self.q_ids_start + 12}": [
                self.availability_ids_start + t - 1
                for t in self.available_during_scheduled_timeslots
            ],  # offset 1
            f"question_{self.q_ids_start + 13}": QuestionChoice.objects.filter(
                question_id=self.q_ids_start + 13,
                value=self.problem_with_NDA,
            )
            .first()
            .pk,
            # "submit": "submit"
        }

    def test_step2(self):
        response = self.client.get("/register/step2")
        self.assertEqual(response.status_code, 200)

    def test_step2_no_github_id(self):
        del self.session["github_id"]
        self.session.save()

        response = self.client.get("/register/step2")

        self.assertEqual(response.status_code, 400)

    def test_step2_form_rendered(self):
        response = self.client.get("/register/step2")
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, self.session["github_email"])
        self.assertContains(response, self.first_name)

    def test_step2_no_github_name(self):
        del self.session["github_name"]
        self.session.save()

        response = self.client.get("/register/step2")

        self.assertEqual(response.status_code, 200)

    def test_step2_github_name_one_word(self):
        self.session["github_name"] = "Sean"
        self.session.save()

        response = self.client.get("/register/step2")

        self.assertEqual(response.status_code, 200)

    def test_post_step2(self):
        response = self.client.post(
            "/register/step2", self.form_data_filled, follow=True
        )

        self.assertRedirects(response, "/")
        self.assertContains(response, "Registration created successfully")

        session = self.client.session
        # check user logged in
        self.assertTrue("_auth_user_id" in session)

        # check session cleanup
        self.assertNotIn("github_id", session)
        self.assertNotIn("github_username", session)
        self.assertNotIn("github_name", session)
        self.assertNotIn("github_email", session)

        user = User.objects.filter(
            github_id=self.session["github_id"],
            github_username=self.session["github_username"],
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email,
            student_number=self.student_number,
        ).first()
        self.assertIsNotNone(user)

        submission = RegistrationSubmission.objects.filter(
            participant=user,
        ).first()
        self.assertIsNotNone(submission)

    def test_post_step2_wrong_student_number(self):
        self.form_data_filled.update(
            {
                f"question_{self.q_ids_start + 3}_student_number": "wrong format",
            }
        )
        response = self.client.post(
            "/register/step2",
            self.form_data_filled,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid Student Number")

    def test_post_step2_requires_fields(self):
        self.form_data_filled.pop(f"question_{self.q_ids_start + 7}")
        response = self.client.post(
            "/register/step2",
            self.form_data_filled,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This field is required.")

    def test_post_step2_existing_user_same_registration(self):
        prior_student_number = "s1337"
        User.objects.create_user(
            github_id=self.github_id,
            github_username=self.github_username,
            student_number=prior_student_number,
        )

        response = self.client.post(
            "/register/step2", self.form_data_filled, follow=True
        )

        self.assertRedirects(response, "/")
        self.assertContains(response, "Registration created successfully")

        new = User.objects.filter(
            student_number=self.student_number,
        ).first()
        self.assertIsNotNone(new)

        old = User.objects.filter(
            student_number=prior_student_number,
        ).first()
        self.assertIsNone(old)

    def test_post_step2_existing_email(self):
        other_lad = User.objects.create_user(
            github_id=123,
            github_username="Jeffrey",
            email=self.email,
        )

        RegistrationSubmission.objects.create(
            registration=Registrations.objects.current_registration(),
            participant=other_lad,
        )

        response = self.client.post(
            "/register/step2",
            self.form_data_filled,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Email address already in use.")

    def test_post_step2_existing_student_number(self):
        other_chum = User.objects.create_user(
            github_id=123,
            github_username="Jeffrey",
            student_number=self.student_number,
        )

        RegistrationSubmission.objects.create(
            registration=Registrations.objects.current_registration(),
            participant=other_chum,
        )

        response = self.client.post(
            "/register/step2",
            self.form_data_filled,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Student Number already in use.")
