"""Tests for awssync.py."""

import json
from unittest.mock import patch

import boto3

import botocore
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
        self.mock_org = mock_organizations()
        self.mock_org.start()

    def tearDown(self):
        self.mock_org.stop()

    def test_button_pressed(self):
        """Test button_pressed function."""
        return_value = self.sync.button_pressed()
        self.assertTrue(return_value)

    def test_create_aws_organization(self):
        moto_client = boto3.client("organizations")
        org = self.sync
        org.create_aws_organization()
        describe_org = moto_client.describe_organization()["Organization"]
        self.assertEqual(describe_org, org.org_info)

    def test_create_aws_organization__exception(self):
        org = self.sync
        with patch("botocore.client.BaseClient._make_api_call", AWSAPITalkerTest.mock_api):
            org.create_aws_organization()
        self.assertTrue(org.fail)
        self.assertIsNone(org.org_info)

    def test_create_course_iteration_OU(self):
        moto_client = boto3.client("organizations")
        org = self.sync
        org.create_aws_organization()
        org.create_course_iteration_OU(1)
        describe_unit = moto_client.describe_organizational_unit(OrganizationalUnitId=org.iterationOU_info["Id"])[
            "OrganizationalUnit"
        ]
        self.assertEqual(describe_unit, org.iterationOU_info)

    def test_create_course_iteration_OU_without_organization(self):
        org = self.sync
        org.create_course_iteration_OU(1)
        self.assertTrue(org.fail)

    def test_create_course_iteration_OU__exception(self):
        org = self.sync
        org.create_aws_organization()
        with patch("botocore.client.BaseClient._make_api_call", AWSAPITalkerTest.mock_api):
            org.create_course_iteration_OU(1)
        self.assertTrue(org.fail)

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

    def test_create_scp_policy__exception(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {
            "Version": "2012-10-17",
            "Statement": [{"Effect": "NonExistentEffect", "Action": "*", "Resource": "*"}],
        }
        with patch("botocore.client.BaseClient._make_api_call", AWSAPITalkerTest.mock_api):
            policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)

        self.assertTrue(self.sync.fail)
        self.assertIsNone(policy)

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


class AWSAPITalkerTest(TestCase):
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
        if operation_name == "CreateOrganizationalUnit":
            raise ClientError(
                {
                    "Error": {
                        "Message": "The OU already exists.",
                        "Code": "ParentNotFoundException",
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
                    "Message": "The OU already exists.",
                },
                "create_organizational_unit",
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
        return botocore.client.BaseClient._make_api_call(self, operation_name, kwarg)


class AWSTreeChecksTest(TestCase):
    """Test checks done on AWSTree data struncture."""

    def setUp(self):
        self.sync = awssync.AWSSync()
        self.awstree = awssync.AWSTree("Name", "1234", [])
        self.iteration = awssync.Iteration("Name", "1234", [])
        self.sync_data = awssync.SyncData("email@example.com", "Project X", "Spring 2020")

        self.sync_list = [
            awssync.SyncData("email1@example.com", "Spring 2022", "Project A"),
            awssync.SyncData("email2@example.com", "Fall 2022", "Project B"),
            awssync.SyncData("email3@example.com", "Spring 2022", "Project C"),
        ]
        self.aws_list = [
            awssync.SyncData("email4@example.com", "Fall 2021", "Project D"),
            awssync.SyncData("email5@example.com", "Spring 2022", "Project E"),
            awssync.SyncData("email6@example.com", "Fall 2022", "Project F"),
        ]

        self.treelist = [
            awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
            awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
            awssync.SyncData("email3@example.com", "project3", "Spring 2021"),
            awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
        ]

        self.aws_tree1 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Spring 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree2 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Fall 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree3 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Fall 2020",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Fall 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

    def test_repr_AWSTree(self):
        self.assertEquals(str(self.awstree), "AWSTree('Name', '1234', [])")

    def test_repr_Iteration(self):
        self.assertEquals(str(self.iteration), "Iteration('Name', '1234', [])")

    def test_repr_SyncData(self):
        self.assertEquals(str(self.sync_data), "SyncData('email@example.com', 'Project X', 'Spring 2020')")

    def test_awstree_to_syncdata_list(self):
        self.assertEqual(self.aws_tree1.awstree_to_syncdata_list(), self.treelist)

    def test_check_for_double_member_email(self):
        # Test when there are no duplicate emails
        self.assertFalse(self.sync.check_for_double_member_email(self.aws_list, self.sync_list))

        # Test when there is a duplicate email
        self.sync_list.append(awssync.SyncData("email4@example.com", "Spring 2022", "Project G"))
        self.assertTrue(self.sync.check_for_double_member_email(self.aws_list, self.sync_list))

    def test_check_current_ou_exists(self):
        # Test when current semester OU does not exist
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Fall 2022"):
            self.assertTrue(Semester.objects.get_or_create_current_semester() == "Fall 2022")
            val1, val2 = self.sync.check_current_ou_exists(self.aws_tree1)
            self.assertEqual((val1, val2), (False, None))

        # Test when current semester OU exists
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2021"):
            self.assertTrue(Semester.objects.get_or_create_current_semester() == "Spring 2021")
            val1, val2 = self.sync.check_current_ou_exists(self.aws_tree1)
            self.assertEqual((val1, val2), (True, "98765"))

    def test_check_members_in_correct_iteration(self):
        # Test when correct
        val1, val2 = self.sync.check_members_in_correct_iteration(self.aws_tree1)
        self.assertEqual((val1, val2), (True, None))

        # Test when incorrect
        val1, val2 = self.sync.check_members_in_correct_iteration(self.aws_tree2)
        self.assertEqual((val1, val2), (False, ["email3@example.com"]))

    def test_check_double_iteration_names(self):
        # Test when correct
        val1, val2 = self.sync.check_double_iteration_names(self.aws_tree1)
        self.assertEqual((val1, val2), (False, None))

        # Test when double
        val1, val2 = self.sync.check_double_iteration_names(self.aws_tree3)
        self.assertEqual((val1, val2), (True, ["Fall 2020"]))

    def test_AWSTree_equals(self):
        self.assertEqual(self.aws_tree1, self.aws_tree1)
        self.assertNotEqual(self.aws_tree1, self.aws_tree2)
        with self.assertRaises(TypeError):
            awssync.AWSTree("", "", []) == []
            self.assertRaises(TypeError)

    def test_Iteration_equals(self):
        self.assertEqual(self.aws_tree1.iterations[0], self.aws_tree1.iterations[0])
        self.assertNotEqual(self.aws_tree1.iterations[0], self.aws_tree1.iterations[1])
        with self.assertRaises(TypeError):
            awssync.Iteration("", "", []) == []
            self.assertRaises(TypeError)
