from unittest.mock import MagicMock, PropertyMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration

User: Employee = get_user_model()


class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first_name = "Test"
        cls.last_name = "Test"
        cls.project_name = "testproject"

        cls.test_user = User.objects.create_user(github_id=1, first_name=cls.first_name, last_name=cls.last_name)

        cls.test_user_2 = User.objects.create_user(
            github_id=2, github_username="testuser2", first_name="Test", last_name="user2"
        )

        cls.test_semester = Semester.objects.get_or_create_current_semester()

        cls.test_project = Project.objects.create(name=cls.project_name, semester=cls.test_semester)

        cls.test_registration = Registration.objects.create(
            user=cls.test_user_2,
            course=Course.objects.sdm(),
            semester=cls.test_semester,
            preference1=cls.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference1="Test partner1",
            partner_preference2="Test partner2",
            partner_preference3="Test partner3",
            is_international=False,
        )

    def test_semester_str(self):
        self.assertEqual(
            f"{self.test_semester.get_season_display()} {self.test_semester.year}", str(self.test_semester)
        )

    def test_registration_is_director_correct(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertTrue(reg.is_director)

    def test_registration_is_director_with_project(self):
        reg = Registration.objects.create(
            user=self.test_user,
            project=self.test_project,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertFalse(reg.is_director)

    def test_registration_is_director_with_sde(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sde(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertFalse(reg.is_director)

    def test_registration_is_director_with_se_and_project(self):
        reg = Registration.objects.create(
            user=self.test_user,
            project=self.test_project,
            course=Course.objects.se(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertFalse(reg.is_director)

    def test_project_str(self):
        self.assertEqual(f"{self.project_name} ({self.test_semester})", str(self.test_project))

    def test__match_partner_name_to_user__complete(self):
        u1 = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        registration = Registration.objects.create(
            user=u1,
            course=Course.objects.se(),
            semester=self.test_semester,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertEqual(registration._match_partner_name_to_user("Test partner 1"), u1)

    def test__match_partner_name_to_user__typo(self):
        u1 = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        registration = Registration.objects.create(
            user=u1,
            course=Course.objects.se(),
            semester=self.test_semester,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertEqual(registration._match_partner_name_to_user("Testpatrner 1"), u1)

    def test__match_partner_name_to_user__no_match(self):
        u1 = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        registration = Registration.objects.create(
            user=u1,
            course=Course.objects.se(),
            semester=self.test_semester,
            experience=Registration.EXPERIENCE_ADVANCED,
            is_international=False,
        )

        self.assertIsNone(registration._match_partner_name_to_user("Abcdefg"))

    def test_partner_preference1_user(self):
        self.test_registration._match_partner_name_to_user = MagicMock(return_value=self.test_user)
        self.assertEqual(self.test_registration.partner_preference1_user, self.test_user)

    def test_partner_preference2_user(self):
        self.test_registration._match_partner_name_to_user = MagicMock(return_value=self.test_user)
        self.assertEqual(self.test_registration.partner_preference2_user, self.test_user)

    def test_partner_preference3_user(self):
        self.test_registration._match_partner_name_to_user = MagicMock(return_value=self.test_user)
        self.assertEqual(self.test_registration.partner_preference3_user, self.test_user)

    def test_get_preferred_partners(self):
        u1 = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        u2 = User.objects.create_user(
            github_id=12, github_username="testpartner2", first_name="Test", last_name="partner 2"
        )
        u3 = User.objects.create_user(
            github_id=13, github_username="testpartner3", first_name="Test", last_name="partner 3"
        )

        with patch("registrations.models.Registration.partner_preference1_user", new_callable=PropertyMock) as m1:
            with patch("registrations.models.Registration.partner_preference2_user", new_callable=PropertyMock) as m2:
                with patch(
                    "registrations.models.Registration.partner_preference3_user", new_callable=PropertyMock
                ) as m3:
                    m1.return_value = User.objects.get(pk=u1.pk)
                    m2.return_value = User.objects.get(pk=u2.pk)
                    m3.return_value = User.objects.get(pk=u3.pk)

                    self.assertQuerysetEqual(
                        self.test_registration.get_preferred_partners(),
                        [repr(u) for u in [u1, u2, u3]],
                        ordered=False,
                    )

    def test_get_partner1_display__match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference1="Test partner 1",
            is_international=False,
        )
        u = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        with patch("registrations.models.Registration.partner_preference1_user", new_callable=PropertyMock) as m1:
            m1.return_value = User.objects.get(pk=u.pk)
            self.assertEqual(reg.get_partner1_display(), u)

    def test_get_partner1_display__no_match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference1="Test partner 1",
            is_international=False,
        )
        with patch("registrations.models.Registration.partner_preference1_user", new_callable=PropertyMock) as m1:
            m1.return_value = None
            self.assertEqual(reg.get_partner1_display(), "'Test partner 1'")

    def test_get_partner1_display__no_preference(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference1=None,
            is_international=False,
        )
        self.assertIsNone(reg.get_partner1_display())

    def test_get_partner2_display__match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference2="Test partner 1",
            is_international=False,
        )
        u = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        with patch("registrations.models.Registration.partner_preference2_user", new_callable=PropertyMock) as m1:
            m1.return_value = User.objects.get(pk=u.pk)
            self.assertEqual(reg.get_partner2_display(), u)

    def test_get_partner2_display__no_match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference2="Test partner 1",
            is_international=False,
        )
        with patch("registrations.models.Registration.partner_preference2_user", new_callable=PropertyMock) as m1:
            m1.return_value = None
            self.assertEqual(reg.get_partner2_display(), "'Test partner 1'")

    def test_get_partner2_display__no_preference(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference2=None,
            is_international=False,
        )
        self.assertIsNone(reg.get_partner2_display())

    def test_get_partner3_display__match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference3="Test partner 1",
            is_international=False,
        )
        u = User.objects.create_user(
            github_id=11, github_username="testpartner1", first_name="Test", last_name="partner 1"
        )
        with patch("registrations.models.Registration.partner_preference3_user", new_callable=PropertyMock) as m1:
            m1.return_value = User.objects.get(pk=u.pk)
            self.assertEqual(reg.get_partner3_display(), u)

    def test_get_partner3_display__no_match(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference3="Test partner 1",
            is_international=False,
        )
        with patch("registrations.models.Registration.partner_preference3_user", new_callable=PropertyMock) as m1:
            m1.return_value = None
            self.assertEqual(reg.get_partner3_display(), "'Test partner 1'")

    def test_get_partner3_display__no_preference(self):
        reg = Registration.objects.create(
            user=self.test_user,
            course=Course.objects.sdm(),
            semester=self.test_semester,
            preference1=self.test_project,
            experience=Registration.EXPERIENCE_ADVANCED,
            partner_preference3=None,
            is_international=False,
        )
        self.assertIsNone(reg.get_partner3_display())
