"""Tests for awssync/checks.py."""
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_iam, mock_organizations, mock_sts

from projects.aws.awssync_checks import Checks
from projects.aws.awssync_checks_permissions import api_permissions
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData


@mock_sts
@mock_organizations
@mock_iam
class ChecksTest(TestCase):
    def setUp(self):
        self.checks = Checks()
        self.aws_tree1 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Spring 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree2 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Fall 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree3 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Fall 2020",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Fall 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

    def test_check_members_in_correct_iteration(self):
        # Test when correct
        self.assertIsNone(self.checks.check_members_in_correct_iteration(self.aws_tree1))

        # Test when incorrect
        self.assertRaises(Exception, self.checks.check_members_in_correct_iteration, self.aws_tree2)

    def test_check_double_iteration_names(self):
        # Test when correct
        self.assertIsNone(self.checks.check_double_iteration_names(self.aws_tree1))

        # Test when double
        self.assertRaises(Exception, self.checks.check_double_iteration_names, self.aws_tree3)

    def mock_simulate_principal_policy(self, allow: bool, api_operations: list[str]):
        return MagicMock(
            return_value={
                "EvaluationResults": [
                    {"EvalActionName": api_operation_name, "EvalDecision": "allowed" if allow else "implicitDeny"}
                    for api_operation_name in api_operations
                ]
            }
        )

    def test_check_aws_api_connection(self):
        self.checks.check_aws_api_connection()

    def test_check_iam_policy(self):
        self.checks.api_talker.iam_client.simulate_principal_policy = self.mock_simulate_principal_policy(
            True, api_permissions
        )
        self.checks.check_iam_policy(api_permissions)

    def test_check_iam_policy__exception(self):
        self.checks.api_talker.iam_client.simulate_principal_policy = self.mock_simulate_principal_policy(
            False, api_permissions
        )
        self.assertRaises(Exception, self.checks.check_iam_policy, api_permissions)

    def test_check_organization_existence(self):
        self.checks.api_talker.create_organization("ALL")
        self.checks.check_organization_existence()

    def test_check_organization_existence__exception(self):
        self.assertRaises(ClientError, self.checks.check_organization_existence)

    def test_check_is_management_account(self):
        self.checks.api_talker.create_organization("ALL")
        self.checks.check_is_management_account()

    def test_check_is_management_account__exception(self):
        self.checks.api_talker.create_organization("ALL")

        mock_identity = self.checks.api_talker.sts_client.get_caller_identity()
        mock_identity["Account"] = "alice123"
        self.checks.api_talker.sts_client.get_caller_identity = MagicMock(return_value=mock_identity)

        self.assertRaises(Exception, self.checks.check_is_management_account)

    def test_check_scp_enabled(self):
        self.checks.api_talker.create_organization("ALL")

        self.checks.api_talker.org_client.enable_policy_type(
            RootId=self.checks.api_talker.list_roots()[0]["Id"],
            PolicyType="SERVICE_CONTROL_POLICY",
        )

        self.checks.check_scp_enabled()

    def test_check_scp_enabled__exception(self):
        self.checks.api_talker.create_organization("ALL")

        args = {
            "RootId": self.checks.api_talker.list_roots()[0]["Id"],
            "PolicyType": "SERVICE_CONTROL_POLICY",
        }

        self.checks.api_talker.org_client.enable_policy_type(**args)
        response = self.checks.api_talker.org_client.disable_policy_type(**args)

        mock_describe_organization = self.checks.api_talker.describe_organization()
        mock_describe_organization["Organization"]["AvailablePolicyTypes"] = response["Root"]["PolicyTypes"]
        self.checks.api_talker.org_client.describe_organization = MagicMock(return_value=mock_describe_organization)

        self.assertRaises(Exception, self.checks.check_scp_enabled)

    def test_pipeline_preconditions(self):
        self.checks.api_talker.create_organization("ALL")

        self.checks.api_talker.iam_client.simulate_principal_policy = self.mock_simulate_principal_policy(
            True, api_permissions
        )

        self.checks.pipeline_preconditions(api_permissions)
