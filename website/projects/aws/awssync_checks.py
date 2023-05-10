from __future__ import annotations

import logging

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_structs import AWSTree


class Checks:
    """Class for pipeline checks."""

    def __init__(self):
        """Initialize an instance with an AWSAPITalker and a logger."""
        self.api_talker = AWSAPITalker()
        self.logger = logging.getLogger("django.aws")

    def check_members_in_correct_iteration(self, AWSdata: AWSTree) -> None:
        """Check if the data from the member tag matches the semester OU it is in."""
        emails_inconsistent_accounts = [
            member.project_email
            for iteration in AWSdata.iterations
            for member in iteration.members
            if member.project_semester != iteration.name
        ]

        if emails_inconsistent_accounts:
            raise Exception(
                f"There are members in a course iteration OU with an inconsistent course iteration tag.\
                      Inconsistent names are {emails_inconsistent_accounts}"
            )

    def check_double_iteration_names(self, AWSdata: AWSTree) -> None:
        """Check if there are multiple OU's with the same name in AWS."""
        names = [iteration.name for iteration in AWSdata.iterations]
        duplicates = [iteration_name for iteration_name in set(names) if names.count(iteration_name) > 1]

        if duplicates:
            raise Exception(
                f"There are multiple course iteration OUs with the same name. Duplicates are: {duplicates}"
            )

    def check_aws_api_connection(self) -> None:
        """Check AWS API connection establishment with current boto3 credentials."""
        self.api_talker.get_caller_identity()

    def check_iam_policy(self, desired_actions: list[str]) -> None:
        """Check permissions for list of AWS API actions."""
        iam_user_arn = self.api_talker.get_caller_identity()["Arn"]
        policy_evaluations = self.api_talker.simulate_principal_policy(iam_user_arn, desired_actions)

        denied_api_actions = [
            evaluation_result["EvalActionName"]
            for evaluation_result in policy_evaluations["EvaluationResults"]
            if evaluation_result["EvalDecision"] != "allowed"
        ]

        if denied_api_actions:
            raise Exception(f"Some AWS API actions have been denied: {denied_api_actions}.")

    def check_organization_existence(self) -> None:
        """Check existence AWS organization."""
        self.api_talker.describe_organization()

    def check_is_management_account(self) -> None:
        """Check if AWS API caller has same effective account ID as the organization's management account."""
        organization_info = self.api_talker.describe_organization()
        iam_user_info = self.api_talker.get_caller_identity()

        management_account_id = organization_info["Organization"]["MasterAccountId"]
        api_caller_account_id = iam_user_info["Account"]
        is_management_account = management_account_id == api_caller_account_id

        if not is_management_account:
            raise Exception("AWS API caller and organization's management account have different account IDs.")

    def check_scp_enabled(self) -> None:
        """Check if SCP policy type feature is enabled for the AWS organization."""
        organization_info = self.api_talker.describe_organization()
        available_policy_types = organization_info["Organization"]["AvailablePolicyTypes"]

        scp_is_enabled = any(
            policy["Type"] == "SERVICE_CONTROL_POLICY" and policy["Status"] == "ENABLED"
            for policy in available_policy_types
        )

        if not scp_is_enabled:
            raise Exception("The SCP policy type is disabled for the organization.")

    def pipeline_preconditions(self, api_permissions: list[str]) -> None:
        """
        Check all crucial pipeline preconditions. Raises exception prematurely on failure.

        Preconditions:
        1. Locatable boto3 credentials and successful AWS API connection
        2. Check allowed AWS API actions based on IAM policy of caller
        3. Existing organization for AWS API caller
        4. AWS API caller acts under same account ID as organization's management account ID
        5. SCP policy type feature enabled for organization
        """
        preconditions = [
            (self.check_aws_api_connection, (), "AWS API connection established"),
            (self.check_iam_policy, (api_permissions,), "AWS API actions permissions"),
            (self.check_organization_existence, (), "AWS organization existence"),
            (self.check_is_management_account, (), "AWS API caller is management account"),
            (self.check_scp_enabled, (), "SCP enabled"),
        ]

        for precondition, args, description in preconditions:
            precondition(*args)
            self.logger.info(f"Pipeline precondition success: {description}.")
