from django.contrib.admin import ACTION_CHECKBOX_NAME
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.shortcuts import reverse
from django.test import Client, TestCase
from django.utils import timezone

from courses.models import Semester, current_season

from projects.models import Project

from registrations.admin import StudentAdminProjectFilter, StudentAdminRoleFilter, StudentAdminSemesterFilter
from registrations.models import GiphouseProfile, Registration, Role

User: DjangoUser = get_user_model()


class RegistrationAdminTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_password = "hunter2"
        cls.admin = User.objects.create_superuser(username="admin", email="", password=cls.admin_password)

        sdm, _ = Role.objects.get_or_create(name=Role.SDM)
        cls.semester, _ = Semester.objects.get_or_create(
            year=timezone.now().year,
            season=current_season(),
            defaults={
                "registration_start": timezone.now() - timezone.timedelta(days=30),
                "registration_end": timezone.now() + timezone.timedelta(days=30),
            },
        )
        project = Project.objects.create(name="GiPHouse1234", description="Test", semester=cls.semester)

        cls.manager = User.objects.create(username="manager")
        GiphouseProfile.objects.create(user=cls.manager, github_id="0", github_username="manager")
        cls.manager.groups.add(sdm)
        cls.manager.save()

        cls.message = {
            "date_joined_0": "2000-12-01",
            "date_joined_1": "12:00:00",
            "initial-date_joined_0": "2000-12-01",
            "initial-date_joined_1": "12:00:00",
            "project": project.id,
            "role": sdm.id,
            "giphouseprofile-TOTAL_FORMS": 1,
            "giphouseprofile-INITIAL_FORMS": 0,
            "giphouseprofile-MIN_NUM_FORMS": 0,
            "giphouseprofile-MAX_NUM_FORMS": 1,
            "giphouseprofile-0-github_id": 4,
            "giphouseprofile-0-github_username": "bob",
            "giphouseprofile-0-student_number": "s0000000",
            "registration_set-TOTAL_FORMS": 1,
            "registration_set-INITIAL_FORMS": 0,
            "registration_set-MIN_NUM_FORMS": 0,
            "registration_set-MAX_NUM_FORMS": 1,
            "registration_set-0-preference1": project.id,
            "registration_set-0-semester": cls.semester.id,
            "registration_set-0-experience": Registration.EXPERIENCE_BEGINNER,
            "_save": "Save",
        }

        cls.registration = Registration.objects.create(
            user=cls.manager, semester=cls.semester, experience=Registration.EXPERIENCE_BEGINNER, preference1=project
        )

        cls.user = User.objects.create(username="user")
        GiphouseProfile.objects.create(user=cls.user, github_id="20", github_username="lol")

    def setUp(self):
        self.client = Client()
        self.client.login(username=self.admin.username, password=self.admin_password)

    def test_get_changelist(self):
        response = self.client.get(reverse("admin:registrations_student_changelist"), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_form(self):
        response = self.client.get(reverse("admin:registrations_student_change", args=[self.manager.id]), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_form_save_with_role_and_project(self):
        response = self.client.post(reverse("admin:registrations_student_add"), self.message, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(giphouseprofile__student_number="s0000000"))

    def test_form_save_without_role_and_project(self):
        self.message["role"] = ""
        self.message["project"] = ""
        response = self.client.post(reverse("admin:registrations_student_add"), self.message, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(User.objects.get(giphouseprofile__student_number="s0000000"))

    def test_project_queryset_contains_projects_from_registration_semester(self):
        response = self.client.get(reverse("admin:auth_user_change", args=[self.manager.pk]))
        self.assertContains(response, "GiPHouse1234")

    def test_place_in_first_project_preference(self):
        response = self.client.post(
            reverse("admin:registrations_student_changelist"),
            {ACTION_CHECKBOX_NAME: [self.manager.pk], "action": "place_in_first_project_preference", "index": 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        project = Project.objects.filter(user=self.manager).first()
        self.assertEqual(project, self.registration.preference1)

    def test_student_change_list_without_registration(self):
        response = self.client.get(reverse("admin:registrations_student_change", args=[self.user.pk]), follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_student_changelist_project_filter(self):
        response = self.client.get(
            reverse("admin:registrations_student_changelist"),
            data={StudentAdminProjectFilter.parameter_name: 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_student_changelist_semester_filter(self):
        response = self.client.get(
            reverse("admin:registrations_student_changelist"),
            data={StudentAdminSemesterFilter.parameter_name: 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)

    def test_get_student_changelist_role_filter(self):
        response = self.client.get(
            reverse("admin:registrations_student_changelist"),
            data={StudentAdminRoleFilter.parameter_name: 0},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
