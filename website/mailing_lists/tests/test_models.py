from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from courses.models import Course, Semester

from mailing_lists.models import ExtraEmailAddress, MailingList, MailingListAlias, MailingListCourseSemesterLink

from projects.models import Project

from registrations.models import Employee, Registration


class ModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_list_address = f"list"
        cls.existing_alias_address = f"alias"
        cls.unused_address = f"unused"

        cls.existing_list = MailingList.objects.create(address=cls.existing_list_address)
        cls.existing_alias = MailingListAlias.objects.create(
            address=cls.existing_alias_address, mailing_list=cls.existing_list
        )

    def test_list_validate_unique_is_valid(self):
        self.existing_list.validate_unique()

    def test_list_validate_unique_alias_exists(self):
        new_mailing_list = MailingList(address=self.existing_alias_address)
        with self.assertRaises(ValidationError):
            new_mailing_list.validate_unique()

    def test_list_email_address(self):
        self.assertEqual(self.existing_list.email_address, self.existing_list_address + "@" + settings.GSUITE_DOMAIN)

    def test_alias_validate_unique_is_valid(self):
        self.existing_alias.validate_unique()

    def test_alias_validate_unique_list_exists(self):
        new_mailing_list = MailingList(address=self.unused_address)
        new_alias = MailingListAlias(address=self.existing_list_address, mailing_list=new_mailing_list)
        with self.assertRaises(ValidationError):
            new_alias.validate_unique()

    def test_alias_validate_unique_parent_list_has_same_email(self):
        shared_email_address = f"collision@{settings.GSUITE_DOMAIN}"
        new_mailing_list = MailingList(address=shared_email_address)
        new_alias = MailingListAlias(address=shared_email_address, mailing_list=new_mailing_list)
        with self.assertRaises(ValidationError):
            new_alias.validate_unique()

    def test_alias_email_address(self):
        self.assertEqual(self.existing_alias.email_address, self.existing_alias_address + "@" + settings.GSUITE_DOMAIN)

    def test_all_addresses_course_semester(self):
        semester = Semester.objects.create(year=2000, season=Semester.FALL)
        course = Course.objects.create(name="Test course")
        project = Project.objects.create(name="test project", semester=semester)

        employee = Employee.objects.create(github_id=0, github_username="user1", email="e@test.nl")
        Registration.objects.create(
            user=employee,
            project=project,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=course,
            preference1=project,
            semester=semester,
        )

        MailingListCourseSemesterLink.objects.create(mailing_list=self.existing_list, course=course, semester=semester)

        self.assertCountEqual(self.existing_list.all_addresses, ["e@test.nl"])

    def test_all_addresses_projects(self):
        semester = Semester.objects.create(year=2000, season=Semester.FALL)
        project = Project.objects.create(name="test project", semester=semester)

        employee = Employee.objects.create(github_id=0, github_username="user1", email="e@test.nl")
        Registration.objects.create(
            user=employee,
            project=project,
            experience=Registration.EXPERIENCE_BEGINNER,
            course=Course.objects.sdm(),
            preference1=project,
            semester=semester,
        )

        self.existing_list.projects.add(project)
        self.existing_list.save()

        self.assertCountEqual(self.existing_list.all_addresses, ["e@test.nl"])

    def test_all_addresses_users(self):
        employee = Employee.objects.create(github_id=0, github_username="user1", email="e@test.nl")
        self.existing_list.users.add(employee)
        self.existing_list.save()

        self.assertCountEqual(self.existing_list.all_addresses, ["e@test.nl"])

    def test_all_addresses_extras(self):
        extra = ExtraEmailAddress.objects.create(address="e@test.nl", name="test", mailing_list=self.existing_list)

        self.assertCountEqual(self.existing_list.all_addresses, [extra.address])

    def test_email_validator_does_block_reserved_address(self):
        try:
            mailinglist1 = MailingList(address="admin")
            mailinglist1.full_clean()
        except ValidationError as e:
            self.assertEqual(e.messages[0], "This is a reserved address")

    def test_email_validator_does_not_block_unreserved_address(self):
        try:
            mailinglist = MailingList(address="admini")
            mailinglist.full_clean()
        except ValidationError:
            self.fail("Mailinglist object raised ValidationError unexpectedly!")
