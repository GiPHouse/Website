from __future__ import annotations

from botocore.exceptions import ClientError

from courses.models import Semester

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_structs import AWSTree, SyncData


class AWSSyncRefactored:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()

    def get_or_create_course_ou(self, tree: AWSTree) -> str:
        """Create organizational unit under root with name of current semester."""
        root_id = tree.ou_id
        course_ou_name = str(Semester.objects.get_or_create_current_semester())
        course_ou_id = next((ou.ou_id for ou in tree.iterations if ou.name == course_ou_name), None)

        if not course_ou_id:
            course_ou = self.api_talker.create_organizational_unit(root_id, course_ou_name)
            course_ou_id = course_ou["OrganizationalUnit"]["Id"]

        return course_ou_id

    def attach_policy(self, target_id: str, policy_id: str) -> None:
        """Attach policy to target resource."""
        try:
            self.api_talker.attach_policy(target_id, policy_id)
        except ClientError as error:
            if error.response["Error"]["Code"] != "DuplicatePolicyAttachmentException":
                raise

    def pipeline_create_account(self, sync_data: SyncData):
        """
        Create a single new AWS member account in the organization of the API caller.

        The status of the member account request is repeatedly checked based on the class' attributes:
            self.ACCOUNT_REQUEST_INTERVAL_SECONDS: thread sleeping time before each status check
            self.ACCOUNT_REQUEST_MAX_ATTEMPTS:     maximum number of times to thread sleep and check

        :param sync_data: SyncData object containing project_email and project_slug.
        :returns:        (True, account_id) on success and otherwise (False, failure_reason).
        """
        client = boto3.client("organizations")
        response_create = client.create_account(
            Email=sync_data.project_email,
            AccountName=sync_data.project_slug,
            IamUserAccessToBilling="DENY",
            Tags=[
                {"Key": "project_slug", "Value": sync_data.project_slug},
                {"Key": "project_semester", "Value": sync_data.project_semester},
            ],
        )
        return response_create

    def pipeline_create_and_move_accounts(self, new_member_accounts, root_id, destination_ou_id):
        """
        Create multiple accounts in the organization of the API caller and move them from the root to a destination OU.

        :param new_member_accounts: List of SyncData objects.
        :param root_id:             The organization's root ID.
        :param destination_ou_id:   The organization's destination OU ID.
        :returns:                   True iff **all** new member accounts were created and moved successfully.
        """
        client = boto3.client("organizations")
        overall_success = True
        for new_member in new_member_accounts:
            # Create member account
            response = self.pipeline_create_account(new_member)
            # Repeatedly check status of new member account request.
            request_id = response["CreateAccountStatus"]["Id"]

            can_move = False

            for _ in range(1, self.ACCOUNT_REQUEST_MAX_ATTEMPTS + 1):
                time.sleep(self.ACCOUNT_REQUEST_INTERVAL_SECONDS)

                try:
                    response_status = client.describe_create_account_status(CreateAccountRequestId=request_id)
                except ClientError as error:
                    self.logger.debug(error)

                request_state = response_status["CreateAccountStatus"]["State"]
                if request_state == "SUCCEEDED":
                    can_move = True
                    account_id = response_status["CreateAccountStatus"]["AccountId"]

            if can_move:

                try:
                    root_id = client.list_roots()["Roots"][0]["Id"]
                    client.move_account(
                        AccountId=account_id, SourceParentId=root_id, DestinationParentId=destination_ou_id
                    )
                except ClientError as error:
                    self.logger.debug(error)
                    overall_success = False
            else:
                failure_reason = response_status["CreateAccountStatus"]["FailureReason"]
                self.logger.debug(failure_reason)
                overall_success = False

        return overall_success
