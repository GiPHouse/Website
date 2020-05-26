from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Course, Semester

from projects.models import Project

from registrations.admin import UserAdminProjectFilter, UserAdminSemesterFilter
from registrations.models import Employee, Registration

User: Employee = get_user_model()


class RegistrationAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(github_id=0, github_username="super")

        cls.course = Course.objects.sdm()

        cls.semester = Semester.objects.get_or_create_current_semester()
        cls.semester.registration_start = timezone.now() - timezone.timedelta(days=30)
        cls.semester.registration_end = timezone.now() + timezone.timedelta(days=30)
        cls.semester.save()

        cls.project = Project.objects.create(name="GiPHouse1234", description="Test", semester=cls.semester)

        cls.manager = User.objects.create(
            github_id=1, github_username="manager", first_name="Man", last_name="Ager", student_number="s1234567"
        )

        cls.registration = Registration.objects.create(
            user=cls.manager,
            project=cls.project,
            semester=cls.semester,
            experience=Registration.EXPERIENCE_BEGINNER,
            preference1=cls.project,
            course=cls.course,
            education_background="background",
            comments="comment",
        )

        cls.user = User.objects.create(
            github_id=2, github_username="lol", first_name="First", last_name="Last", student_number="s1234568"
        )

        cls.message = {
            "date_joined_0": "2000-12-01",
            "date_joined_1": "12:00:00",
            "initial-date_joined_0": "2000-12-01",
            "initial-date_joined_1": "12:00:00",
            "github_id": 4,
            "github_username": "bob",
            "student_number": "s0000000",
            "registration_set-TOTAL_FORMS": 1,
            "registration_set-INITIAL_FORMS": 0,
            "registration_set-MIN_NUM_FORMS": 0,
            "registration_set-MAX_NUM_FORMS": 1,
            "registration_set-0-preference1": cls.project.id,
            "registration_set-0-semester": cls.semester.id,
            "registration_set-0-course": cls.course.id,
            "registration_set-0-project": cls.project.id,
            "registration_set-0-experience": Registration.EXPERIENCE_BEGINNER,
            "registration_set-0-education_background": "background",
            "_save": "Save",
        }

    def setUp(self):
        self.client = Client()
        self.client.force_login(self.admin)

    def test_get_changelist(self):
        response = self.client.get(reverse("admin:registrations_employee_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_form(self):
        response = self.client.get(reverse("admin:registrations_employee_change", args=[self.manager.id]), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_form_save(self):
        response = self.client.post(reverse("admin:registrations_employee_add"), self.message, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(student_number="s0000000"))

    def test_place_in_first_project_preference(self):
        response = self.client.post(
            reverse("admin:registrations_employee_changelist"),
            {ACTION_CHECKBOX_NAME: [self.manager.pk], "action": "place_in_first_project_preference", "index": 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.registration.preference1, Project.objects.filter(registration__user=self.manager))

    def test_student_change_list_without_registration(self):
        response = self.client.get(reverse("admin:registrations_employee_change", args=[self.user.pk]), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_user_changelist_semesterfilter(self):
        response = self.client.get(
            reverse("admin:registrations_employee_changelist"),
            data={
                f"{UserAdminSemesterFilter.field_name}__{UserAdminSemesterFilter.field_pk}__exact": self.semester.id
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_user_changelist_projectfilter(self):
        response = self.client.get(
            reverse("admin:registrations_employee_changelist"),
            data={f"{UserAdminProjectFilter.field_name}__{UserAdminProjectFilter.field_pk}__exact": self.project.id},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_student_number_csv_export(self):
        response = self.client.post(
            reverse("admin:registrations_employee_changelist"),
            {ACTION_CHECKBOX_NAME: [self.user.pk], "action": "export_student_numbers", "index": 0},
        )

        self.assertContains(response, '"First name","Last name","Student number"')
        self.assertContains(response, f'"{self.user.first_name}","{self.user.last_name}","{self.user.student_number}"')
        self.assertEqual(response.status_code, 200)

    def test_registration_csv_export(self):
        response = self.client.post(
            reverse("admin:registrations_employee_changelist"),
            {ACTION_CHECKBOX_NAME: [self.manager.pk], "action": "export_registrations", "index": 0},
        )

        self.assertContains(
            response,
            (
                '"First name","Last name","Student number","GitHub username",'
                '"Course","1st preference","2nd preference","3rd preference",'
                '"Experience","Educational background","Registration Comments"'
            ),
        )
        self.assertContains(
            response,
            (
                f'"{self.manager.first_name}",'
                f'"{self.manager.last_name}",'
                f'"{self.manager.student_number}",'
                f'"{self.manager.github_username}",'
                f'"{self.registration.course}",'
                f'"{self.registration.preference1}",'
                f'"",'
                f'"",'
                f'"{self.registration.experience}",'
                f'"{self.registration.education_background}",'
                f'"{self.registration.comments}"'
            ),
        )
        self.assertEqual(response.status_code, 200)
