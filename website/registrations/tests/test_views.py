from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration

User: Employee = get_user_model()


class RedirectTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_base_url_redirects_to_step_1(self):
        response = self.client.get("/register/")

        self.assertRedirects(response, reverse("registrations:step1"), fetch_redirect_response=False)


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
        self.client.force_login(self.test_user)

        response = self.client.get("/register/step1")

        self.assertRedirects(response, reverse("home"))

    def test_step1_no_semester(self):
        response = self.client.get("/register/step1", follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Registrations are currently not open")

    def test_step1_semester_without_registrations(self):
        Semester.objects.get_or_create_current_semester()

        response = self.client.get("/register/step1", follow=True)

        self.assertRedirects(response, reverse("home"))
        self.assertContains(response, "Registrations are currently not open")

    def test_step1_current_semester_closed_registration(self):
        semester = Semester.objects.get_or_create_current_semester()
        semester.registration_start = timezone.now() - timezone.timedelta(days=2)
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
        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.semester.registration_start = timezone.now()
        cls.semester.registration_end = timezone.now() + timezone.timedelta(days=1)
        cls.semester.save()

        cls.first_name = "FirstTest"
        cls.last_name = "LastTest"
        cls.email = "test@test.com"
        cls.github_username = "test"
        cls.github_id = 1
        cls.student_number = "s1234567"
        cls.experience = Registration.EXPERIENCE_BEGINNER

        cls.project_preference1 = Project.objects.create(
            semester=cls.semester, name="project1", description="Test Project 1"
        )

        cls.project_preference2 = Project.objects.create(
            semester=cls.semester, name="project2", description="Test Project 2"
        )

        cls.project_preference3 = Project.objects.create(
            semester=cls.semester, name="project3", description="Test Project 3"
        )

        cls.se = Course.objects.se()

    def setUp(self):
        self.client = Client()

        self.session = self.client.session
        self.session["github_id"] = self.github_id
        self.session["github_username"] = self.github_username
        self.session["github_email"] = self.email
        self.session["github_name"] = f"{self.first_name} {self.last_name}"

        self.session.save()

    def test_step2(self):
        response = self.client.get("/register/step2")
        self.assertEqual(response.status_code, 200)

    def test_step2_no_github_id(self):
        del self.session["github_id"]
        self.session.save()

        response = self.client.get("/register/step2")

        self.assertEqual(response.status_code, 400)

    def test_step2_includes_initial_information(self):
        response = self.client.get("/register/step2")

        self.assertContains(response, f'value="{self.github_username}"')
        self.assertContains(response, f'value="{self.first_name}"')
        self.assertContains(response, f'value="{self.last_name}"')
        self.assertContains(response, f'value="{self.email}"')

    def test_post_step2(self):
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id + 1,
                "github_username": self.github_username,
                "semester": self.semester.id,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )

        self.assertRedirects(response, "/")
        self.assertContains(response, "Registration created successfully")

    def test_post_step2_wrong_student_number(self):
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": "wrong format",
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertContains(response, "Invalid Student Number")

    def test_post_step2_duplicate_project(self):
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": str(self.project_preference1.id),
            },
            follow=True,
        )
        self.assertContains(response, "You should fill in all preferences with unique values")

    def test_post_step2_existing_user(self):
        existing_user = User.objects.create_user(github_id=self.github_id, student_number=self.student_number)
        Registration.objects.create(
            user=existing_user,
            experience=self.experience,
            course_id=self.se.id,
            preference1_id=self.project_preference1.id,
            preference2_id=self.project_preference2.id,
            preference3_id=self.project_preference3.id,
            semester=Semester.objects.get_or_create_current_semester(),
        )

        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
        )
        self.assertContains(response, "User already registered for this semester.")

    def test_post_step2_existing_user_different_semester(self):
        existing_user = User.objects.create_user(github_id=self.github_id, student_number=self.student_number)

        older_semester = Semester.objects.create(year=timezone.now().year - 2, season=Semester.FALL)

        Registration.objects.create(
            user=existing_user,
            experience=self.experience,
            course_id=self.se.id,
            preference1_id=self.project_preference1.id,
            preference2_id=self.project_preference2.id,
            preference3_id=self.project_preference3.id,
            semester=older_semester,
        )

        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertRedirects(response, "/")
        self.assertContains(response, "Registration created successfully")

    def test_post_step2_existing_email(self):
        existing_user = User.objects.create_user(
            github_id=self.github_id, student_number=self.student_number, email=self.email
        )
        Registration.objects.create(
            user=existing_user,
            experience=self.experience,
            course_id=self.se.id,
            preference1_id=self.project_preference1.id,
            preference2_id=self.project_preference2.id,
            preference3_id=self.project_preference3.id,
            semester=Semester.objects.get_or_create_current_semester(),
        )

        self.session["github_id"] += 1
        self.session.save()

        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id + 1,
                "github_username": self.github_username,
                "experience": self.experience,
                "background": "background",
                "course": self.se.id,
                "email": self.email,
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertContains(response, "Email address already in use")

    def test_step2_works_with_no_last_name(self):
        self.session["github_name"] = f"{self.first_name}"
        self.session.save()
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "semester": self.semester.id,
                "course": self.se.id,
                "email": self.email,
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertRedirects(response, "/")
        self.assertContains(response, "Registration created successfully")

    def test_post_step2_wrong_email(self):
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": f"{self.student_number}@student.ru.nl",
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertContains(response, "Non-existent email address.")

    def test_post_step2_wrong_email2(self):
        response = self.client.post(
            "/register/step2",
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "student_number": self.student_number,
                "github_id": self.github_id,
                "github_username": self.github_username,
                "course": self.se.id,
                "email": f"{self.student_number}@ru.nl",
                "experience": self.experience,
                "background": "background",
                "project1": self.project_preference1.id,
                "project2": self.project_preference2.id,
                "project3": self.project_preference3.id,
            },
            follow=True,
        )
        self.assertContains(response, "Non-existent email address.")
