"""Tests for awssync_refactored.py."""
import json
from unittest.mock import patch


from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_organizations

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.aws.awssync_refactored import AWSSyncRefactored
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData
from projects.models import Project


@mock_organizations
class AWSSyncRefactoredTest(TestCase):
    def setUp(self):
        """Set up testing environment."""
        self.sync = AWSSyncRefactored()
        self.api_talker = self.sync.api_talker

    def test_get_syncdata_from_giphouse_normal(self):
        """Test get_emails_with_teamids function in optimal conditions."""
        self.semester = Semester.objects.create(year=2023, season=Semester.SPRING)
        for i in range(3):
            self.mailing_list = MailingList.objects.create(address="test" + str(i))
            self.project = Project.objects.create(
                id=i, name="test" + str(i), semester=self.semester, slug="test" + str(i)
            )
            self.mailing_list.projects.add(self.project)

        email_id = self.sync.get_syncdata_from_giphouse()

        self.assertIsInstance(email_id, list)
        self.assertIsInstance(email_id[0], SyncData)
        expected_result = [
            SyncData("test0@giphouse.nl", "test0", "Spring 2023"),
            SyncData("test1@giphouse.nl", "test1", "Spring 2023"),
            SyncData("test2@giphouse.nl", "test2", "Spring 2023"),
        ]
        self.assertEqual(email_id, expected_result)

    def test_get_syncdata_from_giphouse_no_project(self):
        """Test get_emails_with_teamids function where the mailinglist is not assigned to a project"""
        MailingList.objects.all().delete()
        self.mailing_list = MailingList.objects.create(address="test2")
        email_id = self.sync.get_syncdata_from_giphouse()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_syncdata_from_giphouse_no_mailing_list(self):
        """Test get_emails_with_teamids function where no mailinglists exist"""
        MailingList.objects.all().delete()
        Project.objects.all().delete()
        email_id = self.sync.get_syncdata_from_giphouse()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_syncdata_from_giphouse_different_semester(self):
        """Test get_emails_with_teamids function where the semester is not equal to the current semester"""
        MailingList.objects.all().delete()
        new_semester = Semester.objects.create(year=2022, season=Semester.FALL)
        self.mailing_list = MailingList.objects.create(address="test4")
        self.project = Project.objects.create(id=4, name="test4", semester=new_semester, slug="test4")
        self.mailing_list.projects.add(self.project)
        email_id = self.sync.get_syncdata_from_giphouse()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_AWS_sync_list_both_empty(self):
        gip_list = []
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_empty_AWS(self):
        test1 = SyncData("test1@test1.test1", "test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2", "test2")
        gip_list = [test1, test2]
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), gip_list)

    def test_AWS_sync_list_empty_GiP(self):
        test1 = SyncData("test1@test1.test1", "test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2", "test2")
        gip_list = []
        aws_list = [test1, test2]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_both_full(self):
        test1 = SyncData("test1@test1.test1", "test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2", "test2")
        test3 = SyncData("test3@test3.test3", "test3", "test3")
        gip_list = [test1, test2]
        aws_list = [test2, test3]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [test1])

    def test_get_tag_value(self):
        tags = [{"Key": "project_semester", "Value": "2021"}, {"Key": "project_slug", "Value": "test1"}]
        self.assertEquals(self.sync.get_tag_value(tags, "project_semester"), "2021")
        self.assertEquals(self.sync.get_tag_value(tags, "project_slug"), "test1")
        self.assertEquals(self.sync.get_tag_value(tags, "project_name"), None)

    def test_extract_aws_setup(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.api_talker.list_roots()[0]["Id"]

        ou_response = self.api_talker.create_organizational_unit(parent_id=root_id, ou_name="OU_1")
        ou_id = ou_response["OrganizationalUnit"]["Id"]

        account_response = self.api_talker.create_account(
            email="account_1@gmail.com",
            account_name="account_1",
            tags=[{"Key": "project_semester", "Value": "2021"}, {"Key": "project_slug", "Value": "test1"}],
        )
        account_id = account_response["CreateAccountStatus"]["AccountId"]
        self.api_talker.move_account(account_id=account_id, source_parent_id=root_id, dest_parent_id=ou_id)

        aws_tree = self.sync.extract_aws_setup(root_id)

        expected_sync_data = [SyncData("account_1@gmail.com", "test1", "2021")]
        expected_iteration = Iteration("OU_1", ou_id, expected_sync_data)
        expected_tree = AWSTree("root", root_id, [expected_iteration])

        self.assertEqual(aws_tree, expected_tree)

    def test_extract_aws_setup_no_slugs(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.api_talker.list_roots()[0]["Id"]

        response_OU_1 = self.api_talker.create_organizational_unit(parent_id=root_id, ou_name="OU_1")
        OU_1_id = response_OU_1["OrganizationalUnit"]["Id"]
        response_account_1 = self.api_talker.create_account(
            email="account_1@gmail.com",
            account_name="account_1",
            tags=[],
        )
        account_id_1 = response_account_1["CreateAccountStatus"]["AccountId"]

        self.api_talker.move_account(account_id=account_id_1, source_parent_id=root_id, dest_parent_id=OU_1_id)

        with self.assertRaises(Exception) as context:
            self.sync.extract_aws_setup(root_id)
        self.assertIn("Found incomplete accounts in AWS", str(context.exception))

    def test_get_or_create_course_ou__new(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]
        tree = AWSTree("root", root_id, [])
        current_semester_name = "Spring 2023"

        with patch.object(Semester.objects, "get_or_create_current_semester", return_value=current_semester_name):
            course_ou_id = self.sync.get_or_create_course_ou(tree)

        course_ou_exists = any(
            ou["Id"] == course_ou_id and ou["Name"] == current_semester_name
            for ou in self.sync.api_talker.list_organizational_units_for_parent(root_id)
        )

        self.assertTrue(course_ou_exists)

    def test_get_or_create_course_ou__already_exists(self):
        tree = AWSTree(
            "root",
            "r-123",
            [
                Iteration("Spring 2023", "ou-456", [SyncData("alice@giphouse.nl", "alices-project", "Spring 2023")]),
                Iteration("Fall 2023", "ou-789", [SyncData("bob@giphouse.nl", "bobs-project", "Fall 2023")]),
            ],
        )

        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2023"):
            course_ou_id = self.sync.get_or_create_course_ou(tree)
        self.assertEqual("ou-456", course_ou_id)

    def test_attach_policy__not_attached(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        new_policy_content = json.dumps(
            {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        )
        new_policy_id = self.sync.api_talker.org_client.create_policy(
            Content=new_policy_content, Description="Deny all access.", Name="DenyAll", Type="SERVICE_CONTROL_POLICY"
        )["Policy"]["PolicySummary"]["Id"]

        self.sync.attach_policy(root_id, new_policy_id)
        attached_policies = self.sync.api_talker.org_client.list_policies_for_target(
            TargetId=root_id, Filter="SERVICE_CONTROL_POLICY"
        )["Policies"]
        attached_policy_ids = [policy["Id"] for policy in attached_policies]

        self.assertIn(new_policy_id, attached_policy_ids)

    def test_attach_policy__caught_exception(self):
        # Error code "DuplicatePolicyAttachmentException" can not be simulated by moto, so it is mocked.
        attach_policy_hard_side_effect = ClientError(
            {"Error": {"Code": "DuplicatePolicyAttachmentException"}}, "attach_policy"
        )
        with patch.object(
            self.sync.api_talker.org_client, "attach_policy", side_effect=attach_policy_hard_side_effect
        ):
            return_value = self.sync.attach_policy("r-123", "p-123")

        self.assertIsNone(return_value)

    def test_attach_policy__reraised_exception(self):
        self.assertRaises(ClientError, self.sync.attach_policy, "r-123", "p-123")
