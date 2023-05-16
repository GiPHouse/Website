from __future__ import annotations

import logging
import time

from botocore.exceptions import ClientError

from courses.models import Semester

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_structs import AWSTree, SyncData


class AWSSyncRefactored:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()

        self.ACCOUNT_REQUEST_INTERVAL_SECONDS = 2
        self.ACCOUNT_REQUEST_MAX_ATTEMPTS = 1

        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)

        self.accounts_created = 0
        self.accounts_moved = 0

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

    def create_and_move_accounts(
        self, new_member_accounts: list[SyncData], root_id: str, destination_ou_id: str
    ) -> bool:
        """
        Create multiple accounts in the organization of the API caller and move them from the root to a destination OU.

        :param new_member_accounts: List of SyncData objects.
        :param root_id:             The organization's root ID.
        :param destination_ou_id:   The organization's destination OU ID.
        :returns:                   True iff **all** new member accounts were created and moved successfully.
        """
        overall_success = True

        for new_member in new_member_accounts:
            # Create member account
            response = self.api_talker.create_account(
                new_member.project_email,
                new_member.project_slug,
                [
                    {"Key": "project_slug", "Value": new_member.project_slug},
                    {"Key": "project_semester", "Value": new_member.project_semester},
                ],
            )
            # Repeatedly check status of new member account request.
            request_id = response["CreateAccountStatus"]["Id"]

            can_move = False

            for _ in range(self.ACCOUNT_REQUEST_MAX_ATTEMPTS):
                time.sleep(self.ACCOUNT_REQUEST_INTERVAL_SECONDS)

                try:
                    response_status = self.api_talker.describe_create_account_status(request_id)
                except ClientError as error:
                    self.logger.debug(error)
                    overall_success = False
                    return overall_success

                request_state = response_status["CreateAccountStatus"]["State"]
                if request_state == "SUCCEEDED":
                    can_move = True
                    account_id = response_status["CreateAccountStatus"]["AccountId"]

            self.accounts_created += 1
            if can_move:

                try:
                    self.api_talker.move_account(account_id, root_id, destination_ou_id)
                    self.accounts_moved += 1
                except ClientError as error:
                    self.logger.debug(error)
                    overall_success = False
            else:
                failure_reason = response_status["CreateAccountStatus"]["FailureReason"]
                self.logger.debug(failure_reason)
                overall_success = False

        return overall_success
