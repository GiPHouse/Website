"""Tests for awssync.py."""
import json
from unittest.mock import MagicMock, patch


from botocore.exceptions import ClientError

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from moto import mock_iam, mock_organizations, mock_sts

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.aws.awssync import AWSSync
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData
from projects.models import AWSPolicy, Project

from registrations.models import Employee

User: Employee = get_user_model()


class QuietAWSSync(AWSSync):
    def __init__(self):
        super().__init__()
        self.logger = MagicMock()


@mock_organizations
@mock_sts
@mock_iam
@patch("projects.admin.AWSSync", new=QuietAWSSync)
class AWSSyncTest(TestCase):
    def setUp(self):
        """Set up testing environment."""
        self.sync = AWSSync()
        self.api_talker = self.sync.api_talker

        self.admin = User.objects.create_superuser(github_id=0, github_username="super")
        self.client = Client()
        self.client.force_login(self.admin)

        self.logger = MagicMock()
        self.sync.logger = self.logger
        self.sync.checker.logger = self.logger

        self.sync.ACCOUNT_REQUEST_INTERVAL_SECONDS = 0.1

    def setup_policy(self):
        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.api_talker.org_client.create_policy(
            Name=policy_name,
            Description=policy_description,
            Content=json.dumps(policy_content),
            Type="SERVICE_CONTROL_POLICY",
            Tags=[{"Key": "no_permissions", "Value": "true"}],
        )
        AWSPolicy.objects.create(
            policy_id=policy["Policy"]["PolicySummary"]["Id"],
            is_current_policy=True,
            tags_key="no_permissions",
            tags_value="true",
        )

    def get_tags_for_account(self, account_email):
        accounts = self.sync.api_talker.org_client.list_accounts()["Accounts"]
        account_id = [account["Id"] for account in accounts if account["Email"] == account_email][0]
        tags = self.api_talker.org_client.list_tags_for_resource(ResourceId=account_id)["Tags"]
        return tags

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
            SyncData("test0@giphouse.nl", "test0"),
            SyncData("test1@giphouse.nl", "test1"),
            SyncData("test2@giphouse.nl", "test2"),
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
        test1 = SyncData("test1@test1.test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2")
        gip_list = [test1, test2]
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), gip_list)

    def test_AWS_sync_list_empty_GiP(self):
        test1 = SyncData("test1@test1.test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2")
        gip_list = []
        aws_list = [test1, test2]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_both_full(self):
        test1 = SyncData("test1@test1.test1", "test1")
        test2 = SyncData("test2@test2.test2", "test2")
        test3 = SyncData("test3@test3.test3", "test3")
        gip_list = [test1, test2]
        aws_list = [test2, test3]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [test1])

    def test_extract_aws_setup(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.api_talker.list_roots()[0]["Id"]

        ou_response = self.api_talker.create_organizational_unit(root_id, "OU_1")
        ou_id = ou_response["OrganizationalUnit"]["Id"]

        account_response = self.api_talker.create_account("account_1@gmail.com", "account_1")
        account_id = account_response["CreateAccountStatus"]["AccountId"]
        self.api_talker.move_account(account_id=account_id, source_parent_id=root_id, dest_parent_id=ou_id)

        aws_tree = self.sync.extract_aws_setup(root_id)

        expected_sync_data = [SyncData("account_1@gmail.com", "account_1")]
        expected_iteration = Iteration("OU_1", ou_id, expected_sync_data)
        expected_tree = AWSTree("root", root_id, [expected_iteration])

        self.assertEqual(aws_tree, expected_tree)

    def test_get_or_create_course_ou__new(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]
        tree = AWSTree("root", root_id, [])

        current_semester_name = str(Semester.objects.get_or_create_current_semester())
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
                Iteration("Spring 2023", "ou-456", [SyncData("alice@giphouse.nl", "alices-project")]),
                Iteration("Fall 2023", "ou-789", [SyncData("bob@giphouse.nl", "bobs-project")]),
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

    def test_get_current_base_ou_id(self):
        test_base_ou_id = "o-123456"
        self.aws_policy = AWSPolicy.objects.create(base_ou_id=test_base_ou_id, is_current_policy=True)
        current_base_ou_id = self.sync.get_current_base_ou_id()
        self.assertEqual(current_base_ou_id, test_base_ou_id)

    def test_get_current_policy_id(self):
        self.policy_id1 = AWSPolicy.objects.create(
            policy_id="Test-Policy1", tags_key="Test-Policy-Id1", is_current_policy=False
        )
        self.policy_id2 = AWSPolicy.objects.create(
            policy_id="Test-Policy2", tags_key="Test-Policy-Id2", is_current_policy=True
        )
        current_policy_id = self.sync.get_current_policy_id()
        self.assertIsInstance(current_policy_id, str)
        self.assertEqual(current_policy_id, self.policy_id2.policy_id)

    def test_get_current_policy__no_current_policy(self):
        self.policy_id1 = AWSPolicy.objects.create(
            policy_id="Test-Policy1", tags_key="Test-Policy-Id1", is_current_policy=False
        )
        self.assertRaises(Exception, self.sync.get_current_base_ou_id)
        self.assertRaises(Exception, self.sync.get_current_policy_id)
        self.assertRaises(Exception, self.sync.get_current_policy_tag)

    def test_get_current_policy_tag__has_key_and_value(self):
        test_key = "not-moved"
        test_val = "pending-move"
        self.aws_policy = AWSPolicy.objects.create(
            policy_id="p-123456", tags_key=test_key, tags_value=test_val, is_current_policy=True
        )
        current_policy_tag = self.sync.get_current_policy_tag()
        self.assertEqual(current_policy_tag, {"Key": test_key, "Value": test_val})

    def test_get_current_policy_tag__has_key_only(self):
        test_key = "not-moved"
        self.aws_policy = AWSPolicy.objects.create(policy_id="p-123456", tags_key=test_key, is_current_policy=True)
        current_policy_tag = self.sync.get_current_policy_tag()
        self.assertEqual(current_policy_tag, {"Key": test_key, "Value": ""})

    def test_create_move_account(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        dest_ou = self.sync.api_talker.create_organizational_unit(root_id, "destination_ou")
        dest_ou_id = dest_ou["OrganizationalUnit"]["Id"]
        members = [
            SyncData("alice@giphouse.nl", "alices-project"),
            SyncData("bob@giphouse.nl", "bobs-project"),
        ]

        self.setup_policy()

        success = self.sync.create_and_move_accounts(members, root_id, dest_ou_id)
        tags_alice = self.get_tags_for_account("alice@giphouse.nl")
        tags_bob = self.get_tags_for_account("bob@giphouse.nl")

        self.assertTrue(success)
        self.assertNotIn({"Key": "no_permissions", "Value": "true"}, tags_alice + tags_bob)

    def test_create_move_account__exception_move(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        dest_ou = self.sync.api_talker.create_organizational_unit(root_id, "destination_ou")
        dest_ou_id = dest_ou["OrganizationalUnit"]["Id"]
        members = [
            SyncData("alice@giphouse.nl", "alices-project"),
            SyncData("bob@giphouse.nl", "bobs-project"),
        ]

        self.setup_policy()
        with patch.object(self.sync.api_talker, "move_account", side_effect=ClientError({}, "move_account")):
            success = self.sync.create_and_move_accounts(members, root_id, dest_ou_id)

        tags_alice = self.get_tags_for_account("alice@giphouse.nl")
        tags_bob = self.get_tags_for_account("bob@giphouse.nl")

        self.assertFalse(success)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_alice)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_bob)

    def test_create_move_account__exception_describe(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        dest_ou = self.sync.api_talker.create_organizational_unit(root_id, "destination_ou")
        dest_ou_id = dest_ou["OrganizationalUnit"]["Id"]
        members = [
            SyncData("alice@giphouse.nl", "alices-project"),
            SyncData("bob@giphouse.nl", "bobs-project"),
        ]

        self.setup_policy()
        with patch.object(
            self.sync.api_talker,
            "describe_create_account_status",
            side_effect=ClientError({}, "describe_create_account_status"),
        ):
            success = self.sync.create_and_move_accounts(members, root_id, dest_ou_id)

        tags_alice = self.get_tags_for_account("alice@giphouse.nl")
        tags_bob = self.get_tags_for_account("bob@giphouse.nl")

        self.assertFalse(success)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_alice)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_bob)

    def test_create_move_account__failed(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        dest_ou = self.sync.api_talker.create_organizational_unit(root_id, "destination_ou")
        dest_ou_id = dest_ou["OrganizationalUnit"]["Id"]
        members = [
            SyncData("alice@giphouse.nl", "alices-project"),
            SyncData("alice@giphouse.nl", "bobs-project"),
        ]

        self.setup_policy()
        with patch.object(
            self.sync.api_talker.org_client,
            "describe_create_account_status",
            return_value={"CreateAccountStatus": {"State": "FAILED", "FailureReason": "EMAIL_ALREADY_EXISTS"}},
        ):
            success = self.sync.create_and_move_accounts(members, root_id, dest_ou_id)

        self.assertFalse(success)

    def test_create_move_account__in_progress(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        dest_ou = self.sync.api_talker.create_organizational_unit(root_id, "destination_ou")
        dest_ou_id = dest_ou["OrganizationalUnit"]["Id"]
        members = [
            SyncData("alice@giphouse.nl", "alices-project"),
            SyncData("bob@giphouse.nl", "bobs-project"),
        ]

        self.setup_policy()
        with patch.object(
            self.sync.api_talker.org_client,
            "describe_create_account_status",
            return_value={"CreateAccountStatus": {"State": "IN_PROGRESS"}},
        ):
            success = self.sync.create_and_move_accounts(members, root_id, dest_ou_id)

        tags_alice = self.get_tags_for_account("alice@giphouse.nl")
        tags_bob = self.get_tags_for_account("bob@giphouse.nl")

        self.assertFalse(success)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_alice)
        self.assertIn({"Key": "no_permissions", "Value": "true"}, tags_bob)

    def test_pipeline__no_accounts_no_ou(self):
        self.sync.checker.api_talker.simulate_principal_policy = MagicMock(
            return_value={"EvaluationResults": [{"EvalDecision": "allowed"}]}
        )
        self.sync.api_talker.create_organization(feature_set="ALL")
        self.setup_policy()

        root_id = self.sync.api_talker.list_roots()[0]["Id"]
        with patch("projects.aws.awssync.AWSSync.get_current_base_ou_id", return_value=root_id):
            pipeline_success = self.sync.pipeline()

        root_ous = self.sync.api_talker.list_organizational_units_for_parent(root_id)
        root_ou_names = [ou["Name"] for ou in root_ous]

        current_semester = str(Semester.objects.get_or_create_current_semester())
        current_accounts = self.sync.api_talker.org_client.list_accounts()["Accounts"]

        self.assertIn(current_semester, root_ou_names)
        self.assertTrue(pipeline_success)

        self.assertEqual(len(current_accounts), 1)
        self.assertEqual(current_accounts[0]["Name"], "master")

    def test_pipeline__new_accounts_existing_ou(self):
        self.sync.checker.api_talker.simulate_principal_policy = MagicMock(
            return_value={"EvaluationResults": [{"EvalDecision": "allowed"}]}
        )
        self.sync.api_talker.create_organization(feature_set="ALL")
        self.setup_policy()

        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        current_semester = str(Semester.objects.get_or_create_current_semester())
        course_ou = self.sync.api_talker.create_organizational_unit(root_id, current_semester)
        course_ou_id = course_ou["OrganizationalUnit"]["Id"]

        self.sync.get_syncdata_from_giphouse = MagicMock(
            return_value=[
                SyncData("alice@giphouse.nl", "alices-project"),
                SyncData("bob@giphouse.nl", "bobs-project"),
            ]
        )

        with patch("projects.aws.awssync.AWSSync.get_current_base_ou_id", return_value=root_id):
            pipeline_success = self.sync.pipeline()

        course_accounts = self.sync.api_talker.list_accounts_for_parent(course_ou_id)
        course_account_emails = [account["Email"] for account in course_accounts]

        self.assertTrue(pipeline_success)
        self.assertEqual(["alice@giphouse.nl", "bob@giphouse.nl"], course_account_emails)

    def test_synchronise__success(self):
        with patch("projects.aws.awssync.AWSSync.pipeline", return_value=True):
            response = self.client.get(reverse("admin:synchronise_to_aws"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sync.SUCCESS_MSG)

    def test_synchronise__failure(self):
        with patch("projects.aws.awssync.AWSSync.pipeline", return_value=False):
            response = self.client.get(reverse("admin:synchronise_to_aws"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sync.FAIL_MSG)

    def test_synchronise__api_error(self):
        api_error = ClientError({"Error": {"Code": "AccessDeniedException"}}, "create_organization")
        with patch("projects.aws.awssync.AWSSync.pipeline", side_effect=api_error):
            response = self.client.get(reverse("admin:synchronise_to_aws"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sync.API_ERROR_MSG)

    def test_synchronise__sync_error(self):
        sync_error = Exception("Synchronization Error")

        with patch("projects.aws.awssync.AWSSync.pipeline", side_effect=sync_error):
            response = self.client.get(reverse("admin:synchronise_to_aws"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.sync.SYNC_ERROR_MSG)
