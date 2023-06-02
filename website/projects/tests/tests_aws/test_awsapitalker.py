import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from moto import mock_organizations, mock_sts

from projects.aws import awsapitalker


@mock_organizations
@mock_sts
class AWSAPITalkerTest(TestCase):
    """Test AWSAPITalker class."""

    def setUp(self):
        """Set up testing environment."""
        self.api_talker = awsapitalker.AWSAPITalker()

    def create_organization(self):
        """Returns the ID of the organization created for testing"""
        org_info = self.api_talker.create_organization("ALL")
        return org_info["Organization"]["Id"]

    def create_dummy_policy_content(self):
        """Returns a string containing the content of a policy used for testing."""
        return json.dumps({"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]})

    def create_dummy_policy(self):
        """
        Creates a policy used for testing.

        :return: ID of the created policy.
        """
        policy_content = self.create_dummy_policy_content()

        return self.api_talker.org_client.create_policy(
            Name="Test policy",
            Content=policy_content,
            Type="SERVICE_CONTROL_POLICY",
            Description="Policy for testing purposes",
        )["Policy"]["PolicySummary"]["Id"]

    def test_create_organization(self):
        response = self.api_talker.create_organization("ALL")

        self.assertEquals(response["Organization"]["FeatureSet"], "ALL")

    def test_create_organizational_unit(self):
        org_id = self.create_organization()

        response = self.api_talker.create_organizational_unit(org_id, "Test OU")

        self.assertEqual(response["OrganizationalUnit"]["Name"], "Test OU")

    def test_attach_policy(self):
        org_id = self.create_organization()

        policy_id = self.create_dummy_policy()

        ou_info = self.api_talker.create_organizational_unit(org_id, "Test OU")
        ou_id = ou_info["OrganizationalUnit"]["Id"]

        self.api_talker.attach_policy(ou_id, policy_id)

        response = self.api_talker.org_client.list_policies_for_target(TargetId=ou_id, Filter="SERVICE_CONTROL_POLICY")
        self.assertIn(policy_id, [p["Id"] for p in response["Policies"]])

    def test_get_caller_identity(self):
        response = self.api_talker.get_caller_identity()
        self.assertIsNotNone(response)

    def test_simulate_principal_policy(self):
        arn = self.api_talker.get_caller_identity()["Arn"]

        with patch.object(
            self.api_talker.iam_client,
            "simulate_principal_policy",
            MagicMock(return_value={"EvaluationResults": [{"EvalDecision": "allowed"}]}),
        ):
            eval_results = self.api_talker.simulate_principal_policy(arn, ["sts:SimulatePrincipalPolicy"])[
                "EvaluationResults"
            ]

        self.assertEquals(eval_results[0]["EvalDecision"], "allowed")

    def test_describe_organization(self):
        self.create_organization()

        response = self.api_talker.describe_organization()

        self.assertIn("Organization", response)
        self.assertIn("MasterAccountId", response["Organization"])
        self.assertIn("MasterAccountEmail", response["Organization"])

    def test_describe_policy(self):
        self.create_organization()

        policy_id = self.create_dummy_policy()

        policy = self.api_talker.describe_policy(policy_id)["Policy"]
        policy_summary = policy["PolicySummary"]
        policy_content = self.create_dummy_policy_content()

        self.assertEquals(policy_summary["Name"], "Test policy")
        self.assertEquals(policy_summary["Description"], "Policy for testing purposes")
        self.assertEquals(policy_content, policy["Content"])

    def test_create_account(self):
        self.create_organization()

        response = self.api_talker.create_account("test@example.com", "Test")

        accounts = self.api_talker.org_client.list_accounts()["Accounts"]

        self.assertEquals(response["CreateAccountStatus"]["AccountName"], "Test")
        self.assertIn(("Test", "test@example.com"), [(account["Name"], account["Email"]) for account in accounts])

    def test_move_account(self):
        org_id = self.create_organization()

        account_status = self.api_talker.create_account("test@example.com", "Test")
        account_id = account_status["CreateAccountStatus"]["AccountId"]

        source_ou_info = self.api_talker.create_organizational_unit(org_id, "Source OU")
        source_ou_id = source_ou_info["OrganizationalUnit"]["Id"]
        dest_ou_info = self.api_talker.create_organizational_unit(org_id, "Destination OU")
        dest_ou_id = dest_ou_info["OrganizationalUnit"]["Id"]

        self.api_talker.move_account(account_id, source_ou_id, dest_ou_id)

        accounts_under_source = self.api_talker.org_client.list_children(ParentId=source_ou_id, ChildType="ACCOUNT")[
            "Children"
        ]
        accounts_under_dest = self.api_talker.org_client.list_children(ParentId=dest_ou_id, ChildType="ACCOUNT")[
            "Children"
        ]
        self.assertNotIn(account_id, [account["Id"] for account in accounts_under_source])
        self.assertIn(account_id, [account["Id"] for account in accounts_under_dest])

    def test_list_organizational_units_for_parent(self):
        self.create_organization()

        root_id = self.api_talker.list_roots()[0]["Id"]

        ou_1 = self.api_talker.create_organizational_unit(root_id, "Test OU 1")["OrganizationalUnit"]
        ou_2 = self.api_talker.create_organizational_unit(root_id, "Test OU 2")["OrganizationalUnit"]

        received_ou_list = self.api_talker.list_organizational_units_for_parent(root_id)

        self.assertCountEqual([ou_1, ou_2], received_ou_list)

    def test_list_accounts_for_parent(self):
        self.create_organization()

        self.api_talker.create_account("test1@example.com", "Test Account 1")
        self.api_talker.create_account("test2@example.com", "Test Account 2")

        root_id = self.api_talker.list_roots()[0]["Id"]

        received_accounts = self.api_talker.list_accounts_for_parent(root_id)
        received_emails = [account["Email"] for account in received_accounts]

        expected_emails = ["master@example.com", "test1@example.com", "test2@example.com"]

        self.assertEqual(expected_emails, received_emails)

    def test_list_tags_for_resource(self):
        org_id = self.create_organization()

        specified_tags = [{"Key": "key1", "Value": "val1"}, {"Key": "key2", "Value": "val2"}]

        response = self.api_talker.create_organizational_unit(org_id, "Test OU", specified_tags)
        ou_id = response["OrganizationalUnit"]["Id"]

        received_tags = self.api_talker.list_tags_for_resource(ou_id)

        self.assertEqual(specified_tags, received_tags)

    def test_list_roots(self):
        self.create_organization()

        roots = self.api_talker.list_roots()

        self.assertTrue(len(roots) == 1)

    def test_describe_create_account_status(self):
        self.create_organization()

        account = self.api_talker.create_account("test@example.com", "Test")
        account_id = account["CreateAccountStatus"]["Id"]

        request = self.api_talker.describe_create_account_status(account_id)
        request_state = request["CreateAccountStatus"]["State"]

        self.assertEqual(request_state, "SUCCEEDED")

    def test_untag_resource(self):
        self.create_organization()

        tag_key = "Test Key"
        tag_value = "Test Value"
        tag = {"Key": tag_key, "Value": tag_value}
        account = self.api_talker.create_account("test@example.com", "Test", [tag])
        account_id = account["CreateAccountStatus"]["AccountId"]

        received_tags = self.api_talker.org_client.list_tags_for_resource(ResourceId=account_id)["Tags"]
        self.assertIn(tag, received_tags)

        self.api_talker.untag_resource(account_id, [tag_key])

        received_tags = self.api_talker.org_client.list_tags_for_resource(ResourceId=account_id)["Tags"]
        self.assertEqual(received_tags, [])
