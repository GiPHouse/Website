"""Tests for awssync.py."""

import json
from unittest.mock import patch

import boto3

from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_organizations

from courses.models import Semester

from mailing_lists.models import MailingList

from projects import awssync
from projects.models import Project


class SyncDataTest(TestCase):
    """Test SyncData class (struct)."""

    def setUp(self):
        """setup test environment."""
        self.sync = awssync.SyncData

    def test_throw_type_error_SyncData_class(self):
        """Test Type Error when equals is called on wrong type."""
        with self.assertRaises(TypeError) as context:
            self.sync("", "", "") == []
        self.assertTrue("Must compare to object of type SyncData" in str(context.exception))


class AWSSyncTest(TestCase):
    """Test AWSSync class."""

    def setUp(self):
        """Set up testing environment."""
        self.sync = awssync.AWSSync()
        self.semester = Semester.objects.create(year=2023, season=Semester.SPRING)
        self.mailing_list = MailingList.objects.create(address="test1")
        self.project = Project.objects.create(id=1, name="test1", semester=self.semester, slug="test1")
        self.mailing_list.projects.add(self.project)

    def test_button_pressed(self):
        """Test button_pressed function."""
        return_value = self.sync.button_pressed()
        self.assertTrue(return_value)

    def test_get_all_mailing_lists(self):
        """Test get_all_mailing_lists function."""
        mailing_lists = self.sync.get_all_mailing_lists()
        self.assertIsInstance(mailing_lists, list)

    def test_get_emails_with_teamids_normal(self):
        """Test get_emails_with_teamids function."""
        email_id = self.sync.get_emails_with_teamids()

        self.assertIsInstance(email_id, list)
        self.assertIsInstance(email_id[0], awssync.SyncData)
        expected_result = [awssync.SyncData("test1@giphouse.nl", "test1", "Spring 2023")]
        self.assertEqual(email_id, expected_result)

    def test_get_emails_with_teamids_no_project(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        self.mailing_list = MailingList.objects.create(address="test2")
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_emails_with_teamids_no_mailing_list(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        Project.objects.all().delete()
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_emails_with_teamids_different_semester(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        new_semester = Semester.objects.create(year=2022, season=Semester.FALL)
        self.mailing_list = MailingList.objects.create(address="test2")
        self.project = Project.objects.create(id=2, name="test2", semester=new_semester, slug="test2")
        self.mailing_list.projects.add(self.project)
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def mock_api(self, operation_name, kwarg):
        if operation_name == "CreateOrganization":
            raise ClientError(
                {
                    "Error": {
                        "Message": "The AWS account is already a member of an organization.",
                        "Code": "AlreadyInOrganizationException",
                    },
                    "ResponseMetadata": {
                        "RequestId": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                        "HTTPStatusCode": 400,
                        "HTTPHeaders": {
                            "x-amzn-requestid": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                            "content-type": "application/x-amz-json-1.1",
                            "content-length": "111",
                            "date": "Sun, 01 Jan 2023 00:00:00 GMT",
                            "connection": "close",
                        },
                        "RetryAttempts": 0,
                    },
                    "Message": "The AWS account is already a member of an organization.",
                },
                "create_organization",
            )

        if operation_name == "CreatePolicy":
            raise ClientError(
                {
                    "Error": {
                        "Message": """The provided policy document does not meet the
                                      requirements of the specified policy type.""",
                        "Code": "MalformedPolicyDocumentException",
                    },
                    "ResponseMetadata": {
                        "RequestId": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                        "HTTPStatusCode": 400,
                        "HTTPHeaders": {
                            "x-amzn-requestid": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                            "content-type": "application/x-amz-json-1.1",
                            "content-length": "147",
                            "date": "Sun, 01 Jan 2023 00:00:00 GMT",
                            "connection": "close",
                        },
                        "RetryAttempts": 0,
                    },
                    "Message": """The provided policy document does not meet the
                                  requirements of the specified policy type.""",
                },
                "create_policy",
            )

    @mock_organizations
    def test_create_aws_organization(self):
        moto_client = boto3.client("organizations")
        org = self.sync
        org.create_aws_organization()
        describe_org = moto_client.describe_organization()["Organization"]
        self.assertEqual(describe_org, org.org_info)

    @patch("botocore.client.BaseClient._make_api_call", mock_api)
    def test_create_aws_organization__exception(self):
        org = self.sync
        org.create_aws_organization()
        self.assertTrue(org.fail)
        self.assertIsNone(org.org_info)

    @mock_organizations
    def test_create_scp_policy(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)

        self.assertFalse(self.sync.fail)
        self.assertEqual(policy["PolicySummary"]["Name"], policy_name)
        self.assertEqual(policy["PolicySummary"]["Description"], policy_description)
        self.assertEqual(policy["Content"], json.dumps(policy_content))

    @mock_organizations
    def test_create_scp_policy__exception(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "NonExistentEffect", "Action": "*", "Resource": "*"}],
        }
        with patch("botocore.client.BaseClient._make_api_call", self.mock_api):
            policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)

        self.assertTrue(self.sync.fail)
        self.assertIsNone(policy)

    @mock_organizations
    def test_attach_scp_policy(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)

        policy_id = policy["PolicySummary"]["Id"]
        root_id = moto_client.list_roots()["Roots"][0]["Id"]
        self.sync.attach_scp_policy(policy_id, root_id)

        current_scp_policies = moto_client.list_policies_for_target(TargetId=root_id, Filter="SERVICE_CONTROL_POLICY")
        current_scp_policy_ids = [scp_policy["Id"] for scp_policy in current_scp_policies["Policies"]]

        self.assertIn(policy_id, current_scp_policy_ids)
        self.assertFalse(self.sync.fail)

    @mock_organizations
    def test_attach_scp_policy__exception(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)

        policy_id = policy["PolicySummary"]["Id"]
        root_id = self.sync.org_info["Id"]  # Retrieves organization ID, not root ID, resulting in ClientError.
        self.sync.attach_scp_policy(policy_id, root_id)

        self.assertTrue(self.sync.fail)


class AWSSyncListTest(TestCase):
    """Test AWSSyncList class."""

    def setUp(self):
        self.sync = awssync.AWSSync()
        self.syncData = awssync.SyncData

        self.test1 = self.syncData("test1@test1.test1", "test1", "test1")
        self.test2 = self.syncData("test2@test2.test2", "test2", "test2")
        self.test3 = self.syncData("test3@test3.test3", "test3", "test3")

    def test_AWS_sync_list_both_empty(self):
        gip_list = []
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_empty_AWS(self):
        gip_list = [self.test1, self.test2]
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), gip_list)

    def test_AWS_sync_list_empty_GiP(self):
        gip_list = []
        aws_list = [self.test1, self.test2]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_both_full(self):
        gip_list = [self.test1, self.test2]
        aws_list = [self.test2, self.test3]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [self.test1])
