"""Tests for awssync.py."""

import json
from unittest.mock import MagicMock, patch

import boto3

import botocore
from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_organizations, mock_sts

from courses.models import Semester

from mailing_lists.models import MailingList

from projects import awssync
from projects.models import Project


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

    def simulateFailure(self):
        self.sync.fail = True

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
        org.create_course_iteration_OU("1")
        describe_unit = moto_client.describe_organizational_unit(OrganizationalUnitId=org.iterationOU_info["Id"])[
            "OrganizationalUnit"
        ]
        self.assertEqual(describe_unit, org.iterationOU_info)

    def test_create_course_iteration_OU_without_organization(self):
        org = self.sync
        org.create_course_iteration_OU("1")
        self.assertTrue(org.fail)

    def test_create_course_iteration_OU__exception(self):
        org = self.sync
        org.create_aws_organization()
        with patch("boto3.client") as mocker:
            mocker().list_roots.side_effect = ClientError({}, "list_roots")
            org.create_course_iteration_OU("1")
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

    @mock_sts
    def test_check_aws_api_connection(self):
        success, caller_identity_info = self.sync.check_aws_api_connection()

        self.assertTrue(success)
        self.assertIsNotNone(caller_identity_info)

    @mock_sts
    def test_check_aws_api_connection__exception(self):
        with patch("boto3.client") as mocker:
            mocker.get_caller_identity.side_effect = ClientError({}, "get_caller_identity")
            mocker.return_value = mocker
            success, caller_identity_info = self.sync.check_aws_api_connection()

        self.assertFalse(success)
        self.assertIsNone(caller_identity_info)

    # IAM simulate_principal_policy is not covered by moto.
    def test_check_iam_policy(self):
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        # success == True
        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            success = self.sync.check_iam_policy(iam_user_arn, desired_actions)
        self.assertTrue(success)

        # success == False
        mock_evaluation_results["EvaluationResults"][0]["EvalDecision"] = "implicitDeny"
        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            success = self.sync.check_iam_policy(iam_user_arn, desired_actions)
        self.assertFalse(success)

    def test_check_iam_policy__exception(self):
        iam_user_arn = "daddy"
        desired_actions = []

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.side_effect = ClientError({}, "simulate_principal_policy")
            success = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        self.assertFalse(success)

    def test_check_organization_existence(self):
        moto_client = boto3.client("organizations")
        organization_create_info = moto_client.create_organization(FeatureSet="ALL")["Organization"]
        success, organization_describe_info = self.sync.check_organization_existence()

        self.assertTrue(success)
        self.assertEqual(organization_create_info, organization_describe_info)

    def test_check_organization_existence__exception(self):
        with patch("boto3.client") as mocker:
            mocker.describe_organization.side_effect = ClientError({}, "describe_organization")
            mocker.return_value = mocker
            success, organization_info = self.sync.check_organization_existence()

        self.assertFalse(success)
        self.assertIsNone(organization_info)

    @mock_sts
    def test_check_is_management_account(self):
        moto_client = boto3.client("organizations")

        moto_client.create_organization(FeatureSet="ALL")["Organization"]
        _, caller_identity_info = self.sync.check_aws_api_connection()
        _, organization_info = self.sync.check_organization_existence()

        # is_management_account == True
        success_acc = self.sync.check_is_management_account(caller_identity_info, organization_info)
        self.assertTrue(success_acc)

        # is_management_account == False
        caller_identity_info["Account"] = "daddy"
        success_acc = self.sync.check_is_management_account(caller_identity_info, organization_info)
        self.assertFalse(success_acc)

    def test_check_scp_enabled(self):
        moto_client = boto3.client("organizations")

        # SCP enabled.
        organization_info = moto_client.create_organization(FeatureSet="ALL")["Organization"]
        scp_is_enabled = self.sync.check_scp_enabled(organization_info)
        self.assertTrue(scp_is_enabled)

        # SCP semi-disabled (pending).
        organization_info["AvailablePolicyTypes"][0]["Status"] = "PENDING_DISABLE"
        scp_is_enabled = self.sync.check_scp_enabled(organization_info)
        self.assertFalse(scp_is_enabled)

        # SCP disabled (empty list).
        organization_info["AvailablePolicyTypes"] = []
        scp_is_enabled = self.sync.check_scp_enabled(organization_info)
        self.assertFalse(scp_is_enabled)

    @mock_sts
    def test_pipeline_preconditions__all_success(self):
        # Create organization.
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        # Mock return value of simulate_principal_policy.
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_iam_policy = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        # Mock return value of check_iam_policy.
        with patch("projects.awssync.AWSSync.check_iam_policy") as mocker:
            mocker.return_value = check_iam_policy
            success = self.sync.pipeline_preconditions()

        self.assertTrue(success)

    @mock_sts
    def test_pipeline_preconditions__no_connection(self):
        with patch("boto3.client") as mocker:
            mocker.get_caller_identity.side_effect = ClientError({}, "get_caller_identity")
            mocker.return_value = mocker
            success = self.sync.pipeline_preconditions()

        self.assertFalse(success)

    def test_pipeline_preconditions__no_iam(self):
        # Mock return value of simulate_principal_policy.
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "implicitDeny",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_api_actions = self.sync.check_iam_policy(iam_user_arn, desired_actions)

            # Mock return value of check_iam_policy.
            with patch("projects.awssync.AWSSync.check_iam_policy") as mocker:
                mocker.return_value = check_api_actions
                success = self.sync.pipeline_preconditions()

        self.assertFalse(success)

    @mock_sts
    def test_pipeline_preconditions__no_organization(self):
        # Mock return value of simulate_principal_policy.
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_iam_policy = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        # Mock return value of check_iam_policy.
        with patch("projects.awssync.AWSSync.check_iam_policy") as mocker:
            mocker.return_value = check_iam_policy
            success = self.sync.pipeline_preconditions()

        self.assertFalse(success)

    @mock_sts
    def test_pipeline_preconditions__no_management(self):
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")

        # Mock return value of simulate_principal_policy.
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_iam_policy = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        # Mock return value of check_iam_policy.
        with patch("projects.awssync.AWSSync.check_iam_policy") as mocker_iam:
            mocker_iam.return_value = check_iam_policy
            with patch("projects.awssync.AWSSync.check_aws_api_connection") as mocker_api:
                mocker_api.return_value = True, {"Account": "daddy", "Arn": "01234567890123456789"}
                success = self.sync.pipeline_preconditions()

        self.assertFalse(success)

    @mock_sts
    def test_pipeline_preconditions__no_scp(self):
        moto_client = boto3.client("organizations")

        organization_info = moto_client.create_organization(FeatureSet="ALL")["Organization"]

        # Mock return value of simulate_principal_policy.
        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_iam_policy = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        # Mock return value of check_iam_policy.
        with patch("projects.awssync.AWSSync.check_iam_policy") as mocker_iam:
            mocker_iam.return_value = check_iam_policy

            # Mock return value of check_organization_existence with no SCP policy enabled.
            organization_info["AvailablePolicyTypes"] = []
            with patch("projects.awssync.AWSSync.check_organization_existence") as mocker:
                mocker.return_value = True, organization_info
                success = self.sync.pipeline_preconditions()

        self.assertFalse(success)

    """
    def test_pipeline_create_scp_policy(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}

        policy = self.sync.pipeline_create_scp_policy()

        self.assertFalse(self.sync.fail)
        self.assertEqual(policy["PolicySummary"]["Name"], policy_name)
        self.assertEqual(policy["PolicySummary"]["Description"], policy_description)
        self.assertEqual(policy["Content"], json.dumps(policy_content))

    def test_pipeline_create_scp_policy__exception(self):
        self.sync.create_aws_organization()

        with patch("botocore.client.BaseClient._make_api_call", AWSAPITalkerTest.mock_api):
            policy = self.sync.pipeline_create_scp_policy()

        self.assertTrue(self.sync.fail)
        self.assertIsNone(policy)
    """

    def test_pipeline_policy(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)
        self.sync.policy_id = policy["PolicySummary"]["Id"]

        ou_id = self.sync.create_course_iteration_OU("Test")

        success = self.sync.pipeline_policy(ou_id)
        self.assertTrue(success)

    def test_pipeline_policy__exception(self):
        self.sync.create_aws_organization()

        ou_id = self.sync.create_course_iteration_OU("Test")

        success = self.sync.pipeline_policy(ou_id)
        self.assertFalse(success)

    def test_pipeline_policy__failure_attach(self):
        self.sync.create_aws_organization()

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)
        self.sync.policy_id = policy["PolicySummary"]["Id"]

        ou_id = self.sync.create_course_iteration_OU("Test")

        self.sync.attach_scp_policy = MagicMock(side_effect=self.simulateFailure())

        success = self.sync.pipeline_policy(ou_id)
        self.assertFalse(success)

    @mock_sts
    def test_pipeline(self):
        moto_client = boto3.client("organizations")

        # pipeline_preconditions() == False
        success = self.sync.pipeline()
        self.assertFalse(success)

        # pipeline_preconditions() == True
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        policy_name = "DenyAll"
        policy_description = "Deny all access."
        policy_content = {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        policy = self.sync.create_scp_policy(policy_name, policy_description, policy_content)
        self.sync.policy_id = policy["PolicySummary"]["Id"]

        iam_user_arn = "daddy"
        desired_actions = []
        mock_evaluation_results = {
            "EvaluationResults": [
                {
                    "EvalActionName": "organizations:CreateOrganizationalUnit",
                    "EvalDecision": "allowed",
                    "EvalResourceName": "*",
                    "MissingContextValues": [],
                }
            ]
        }

        with patch("boto3.client") as mocker:
            mocker().simulate_principal_policy.return_value = mock_evaluation_results
            check_iam_policy = self.sync.check_iam_policy(iam_user_arn, desired_actions)

        with patch("projects.awssync.AWSSync.check_iam_policy") as mocker:
            mocker.return_value = check_iam_policy
            success = self.sync.pipeline()

        self.assertTrue(success)

    def test_pipeline__exception_list_roots(self):
        self.sync.pipeline_preconditions = MagicMock(return_value=True)

        with patch("boto3.client") as mocker:
            mocker().list_roots.side_effect = ClientError({}, "list_roots")
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__edge_case_double_emails(self):
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        aws_tree = awssync.AWSTree(
            "Root",
            "123",
            [
                awssync.Iteration(
                    "Spring 2023",
                    "456",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Spring 2023"),
                    ],
                )
            ],
        )

        gip_teams = [
            awssync.SyncData("email1@example.com", "project1", "Spring 2023"),
            awssync.SyncData("email1@example.com", "project2", "Spring 2023"),
        ]

        self.sync.pipeline_preconditions = MagicMock(return_value=True)
        self.sync.extract_aws_setup = MagicMock(return_value=aws_tree)
        self.sync.get_emails_with_teamids = MagicMock(return_value=gip_teams)
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2023"):
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__edge_case_incorrectly_placed(self):
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        aws_tree = awssync.AWSTree(
            "Root",
            "123",
            [
                awssync.Iteration(
                    "Fall 2023",
                    "456",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Spring 2023"),
                    ],
                )
            ],
        )

        gip_teams = [awssync.SyncData("email1@example.com", "project1", "Spring 2023")]

        self.sync.pipeline_preconditions = MagicMock(return_value=True)
        self.sync.extract_aws_setup = MagicMock(return_value=aws_tree)
        self.sync.get_emails_with_teamids = MagicMock(return_value=gip_teams)
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2023"):
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__edge_case_double_iteration_names(self):
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        aws_tree = awssync.AWSTree(
            "Root",
            "123",
            [
                awssync.Iteration(
                    "Spring 2023", "456", [awssync.SyncData("email1@example.com", "project1", "Spring 2023")]
                ),
                awssync.Iteration("Spring 2023", "789", []),
            ],
        )

        gip_teams = [awssync.SyncData("email1@example.com", "project1", "Spring 2023")]

        self.sync.pipeline_preconditions = MagicMock(return_value=True)
        self.sync.extract_aws_setup = MagicMock(return_value=aws_tree)
        self.sync.get_emails_with_teamids = MagicMock(return_value=gip_teams)
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2023"):
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__failed_creating_iteration_ou(self):
        moto_client = boto3.client("organizations")
        moto_client.create_organization(FeatureSet="ALL")["Organization"]

        self.sync.pipeline_preconditions = MagicMock(return_value=True)
        with patch("boto3.client") as mocker:
            mocker().create_organizational_unit.side_effect = ClientError({}, "create_organizational_unit")
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__exception_attaching_policy(self):
        self.sync.create_aws_organization()
        self.sync.pipeline_preconditions = MagicMock(return_value=True)

        with patch("boto3.client") as mocker:
            mocker().attach_policy.side_effect = ClientError(
                {"Error": {"Code": "PolicyTypeNotEnabledException"}}, "attach_policy"
            )
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__already_attached_policy(self):
        self.sync.create_aws_organization()
        self.sync.pipeline_preconditions = MagicMock(return_value=True)

        with patch("boto3.client") as mocker:
            mocker().attach_policy.side_effect = ClientError(
                {"Error": {"Code": "DuplicatePolicyAttachmentException"}}, "attach_policy"
            )
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__failed_create_and_move_account(self):
        self.sync.create_aws_organization()
        self.sync.pipeline_preconditions = MagicMock(return_value=True)

        with patch("boto3.client") as mocker:
            mocker().move_account.side_effect = ClientError({}, "move_account")
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline__exception_extract_aws_setup(self):
        self.sync.pipeline_preconditions = MagicMock(return_value=True)

        with patch("boto3.client") as mocker:
            mocker().list_organizational_units_for_parent.side_effect = ClientError(
                {}, "list_organizational_units_for_parent"
            )
            success = self.sync.pipeline()

        self.assertFalse(success)

    def test_pipeline_update_current_course_iteration_ou___failure_check_current_ou(self):

        self.sync.check_current_ou_exists = MagicMock(return_value=(False, None))

        self.sync.create_aws_organization()
        success, id = self.sync.pipeline_update_current_course_iteration_ou(None)
        self.assertTrue(success)
        self.assertFalse(id is None)

    def test_pipeline_update_current_course_iteration_ou___success(self):

        self.sync.check_current_ou_exists = MagicMock(return_value=(True, "1234"))

        self.sync.create_aws_organization()
        success, id = self.sync.pipeline_update_current_course_iteration_ou(None)
        self.assertTrue(success)
        self.assertEquals(id, "1234")

    def test_pipeline_update_current_course_iteration_ou___failure_create_ou(self):

        self.sync.check_current_ou_exists = MagicMock(return_value=(False, None))
        self.sync.create_course_iteration_OU = MagicMock(side_effect=self.simulateFailure())

        self.sync.create_aws_organization()
        success, failure_reason = self.sync.pipeline_update_current_course_iteration_ou(None)

        self.assertFalse(success)
        self.assertEquals(failure_reason, "ITERATION_OU_CREATION_FAILED")
        self.assertTrue(self.sync.fail)

    def test_pipeline_create_account(self):
        self.sync.create_aws_organization()

        response = self.sync.pipeline_create_account(
            awssync.SyncData("alice@example.com", "alice", "Spring 2023")
        )

        self.assertIsNotNone(response)

    def test_pipeline_create_account__exception_create_account(self):
        self.sync.create_aws_organization()

        with patch("boto3.client") as mocker:
            mocker().create_account.side_effect = ClientError({}, "create_account")
            response = self.sync.pipeline_create_account(
                awssync.SyncData("alice@example.com", "alice", "Spring 2023")
            )
        self.assertEquals(response, "CLIENTERROR_CREATE_ACCOUNT")

    def test_pipeline_create_account__exception_describe_account_status(self):
        self.sync.create_aws_organization()

        with patch("boto3.client") as mocker:
            mocker().describe_create_account_status.side_effect = ClientError({}, "describe_create_account_status")
            response = self.sync.pipeline_create_account(
                awssync.SyncData("alice@example.com", "alice", "Spring 2023")
            )

        self.assertEquals(response, "CLIENTERROR_DESCRIBE_CREATE_ACCOUNT_STATUS")

    def test_pipeline_create_account__state_failed(self):
        self.sync.create_aws_organization()

        with patch("boto3.client") as mocker:
            response = {"CreateAccountStatus": {"State": "FAILED", "FailureReason": "EMAIL_ALREADY_EXISTS"}}
            mocker().describe_create_account_status.return_value = response
            response = self.sync.pipeline_create_account(
                awssync.SyncData("alice@example.com", "alice", "Spring 2023")
            )
        self.assertEquals(response, "EMAIL_ALREADY_EXISTS")

    def test_pipeline_create_account__state_in_progress(self):
        self.sync.create_aws_organization()

        with patch("boto3.client") as mocker:
            response = {
                "CreateAccountStatus": {
                    "State": "IN_PROGRESS",
                }
            }
            mocker().describe_create_account_status.return_value = response
            response = self.sync.pipeline_create_account(
                awssync.SyncData("alice@example.com", "alice", "Spring 2023")
            )

        self.assertEquals(response, "STILL_IN_PROGRESS")

    def test_pipeline_create_and_move_accounts(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()

        new_member_accounts = [
            awssync.SyncData("alice@example.com", "alice", "Spring 2023"),
            awssync.SyncData("bob@example.com", "bob", "Spring 2023"),
        ]
        root_id = moto_client.list_roots()["Roots"][0]["Id"]
        course_iteration_id = self.sync.create_course_iteration_OU("Spring 2023")

        success = self.sync.pipeline_create_and_move_accounts(new_member_accounts, root_id, course_iteration_id)
        self.assertTrue(success)

    def test_pipeline_create_and_move_accounts__email_exists(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()

        new_member_accounts = [("alice@example.com", "alice"), ("bob@example.com", "bob")]
        root_id = moto_client.list_roots()["Roots"][0]["Id"]
        course_iteration_id = self.sync.create_course_iteration_OU("2023Fall")

        with patch("projects.awssync.AWSSync.pipeline_create_account") as mocker:
            mocker.return_value = False, "EMAIL_ALREADY_EXISTS"
            success = self.sync.pipeline_create_and_move_accounts(new_member_accounts, root_id, course_iteration_id)

        self.assertFalse(success)

    def test_pipeline_create_and_move_accounts__exception_move_account(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()

        new_member_accounts = [("alice@example.com", "alice"), ("bob@example.com", "bob")]
        root_id = moto_client.list_roots()["Roots"][0]["Id"]
        course_iteration_id = self.sync.create_course_iteration_OU("2023Fall")

        self.sync.pipeline_create_account = MagicMock(return_value=(True, 1234))
        with patch("boto3.client") as mocker:
            mocker().move_account.side_effect = ClientError({}, "move_account")
            success = self.sync.pipeline_create_and_move_accounts(new_member_accounts, root_id, course_iteration_id)

        self.assertFalse(success)

    @mock_organizations
    def test_get_aws_data(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()
        root_id = moto_client.list_roots()["Roots"][0]["Id"]

        response_OU_1 = moto_client.create_organizational_unit(ParentId=root_id, Name="OU_1")
        OU_1_id = response_OU_1["OrganizationalUnit"]["Id"]
        response_account_1 = moto_client.create_account(
            Email="account_1@gmail.com",
            AccountName="account_1",
            Tags=[{"Key": "project_semester", "Value": "2021"}, {"Key": "project_slug", "Value": "test1"}],
        )
        account_id_1 = response_account_1["CreateAccountStatus"]["AccountId"]
        moto_client.move_account(AccountId=account_id_1, SourceParentId=root_id, DestinationParentId=OU_1_id)

        aws_tree = self.sync.extract_aws_setup(root_id)
        iteration_test = awssync.Iteration("OU_1", OU_1_id, [awssync.SyncData("account_1@gmail.com", "test1", "2021")])
        aws_tree_test = awssync.AWSTree("root", root_id, [iteration_test])
        self.assertEquals(aws_tree, aws_tree_test)

    @mock_organizations
    def test_get_aws_data_no_root(self):
        boto3.client("organizations")
        self.sync.create_aws_organization()
        self.sync.extract_aws_setup("NonExistentRootID")
        self.assertTrue(self.sync.fail)

    @mock_organizations
    def test_get_aws_data_no_slugs(self):
        moto_client = boto3.client("organizations")
        self.sync.create_aws_organization()
        root_id = moto_client.list_roots()["Roots"][0]["Id"]

        response_OU_1 = moto_client.create_organizational_unit(ParentId=root_id, Name="OU_1")
        OU_1_id = response_OU_1["OrganizationalUnit"]["Id"]
        response_account_1 = moto_client.create_account(
            Email="account_1@gmail.com",
            AccountName="account_1",
            Tags=[],
        )
        account_id_1 = response_account_1["CreateAccountStatus"]["AccountId"]
        moto_client.move_account(AccountId=account_id_1, SourceParentId=root_id, DestinationParentId=OU_1_id)
        self.sync.extract_aws_setup(root_id)
        self.assertTrue(self.sync.fail)


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
