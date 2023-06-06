from __future__ import annotations

import logging
import time

from botocore.exceptions import ClientError

from django.contrib import messages

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_checks import Checks
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData
from projects.models import AWSPolicy, Project


class AWSSync:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()
        self.checker = Checks()
        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)

        self.ACCOUNT_REQUEST_INTERVAL_SECONDS = 5
        self.ACCOUNT_REQUEST_MAX_ATTEMPTS = 3

        self.SUCCESS_MSG = "Successfully synchronized all projects to AWS."
        self.FAIL_MSG = "Not all accounts were created and moved successfully. Check the console for more information."
        self.API_ERROR_MSG = "An error occurred while calling the AWS API. Check the console for more information."
        self.SYNC_ERROR_MSG = (
            "An error occurred during synchronization with AWS. Check the console for more information"
        )

    def get_syncdata_from_giphouse(self) -> list[SyncData]:
        """
        Create a list of SyncData struct containing email, slug.

        :return: list of SyncData structs with email, slug
        """
        sync_data_list = []
        current_semester = Semester.objects.get_or_create_current_semester()

        for project in Project.objects.filter(mailinglist__isnull=False, semester=current_semester).values(
            "slug", "mailinglist"
        ):
            project_slug = project["slug"]
            project_email = MailingList.objects.get(pk=project["mailinglist"]).email_address

            sync_data = SyncData(project_email, project_slug)
            sync_data_list.append(sync_data)
        return sync_data_list

    def generate_aws_sync_list(self, giphouse_data: list[SyncData], aws_data: list[SyncData]) -> list[SyncData]:
        """
        Generate the list of users that are registered on the GiPhouse website, but are not yet invited for AWS.

        This includes their ID and email address, to be able to put users in the correct AWS organization later.
        """
        return [project for project in giphouse_data if project not in aws_data]

    def extract_aws_setup(self, parent_ou_id: str) -> AWSTree:
        """
        Give a list of all the children of the parent OU.

        :param parent_ou_id: The ID of the parent OU.
        :return: A AWSTree object containing all the children of the parent OU.
        """
        aws_tree = AWSTree(
            "root",
            parent_ou_id,
            [
                Iteration(
                    ou["Name"],
                    ou["Id"],
                    [
                        SyncData(account["Email"], account["Name"])
                        for account in self.api_talker.list_accounts_for_parent(parent_id=ou["Id"])
                    ],
                )
                for ou in self.api_talker.list_organizational_units_for_parent(parent_id=parent_ou_id)
            ],
        )

        return aws_tree

    def get_or_create_course_ou(self, tree: AWSTree) -> str:
        """Create organizational unit under root with name of current semester."""
        root_id = tree.ou_id
        course_ou_name = str(Semester.objects.get_or_create_current_semester())
        course_ou_id = next((ou.ou_id for ou in tree.iterations if ou.name == course_ou_name), None)

        if not course_ou_id:
            course_ou = self.api_talker.create_organizational_unit(root_id, course_ou_name)
            course_ou_id = course_ou["OrganizationalUnit"]["Id"]
            self.logger.info(f"Created semester OU '{course_ou_name}' with ID '/{root_id}/{course_ou_id}'.")
        else:
            self.logger.info(f"Semester OU '{course_ou_name}' exists with ID '/{root_id}/{course_ou_id}'.")

        return course_ou_id

    def attach_policy(self, target_id: str, policy_id: str) -> None:
        """Attach policy to target resource."""
        try:
            self.api_talker.attach_policy(target_id, policy_id)
            self.logger.info(f"Attached policy with ID '{policy_id}' to target ID '{target_id}'.")
        except ClientError as error:
            if error.response["Error"]["Code"] != "DuplicatePolicyAttachmentException":
                raise
            self.logger.info(f"Policy with ID '{policy_id}' is already attached to target ID '{target_id}'.")

    def get_current_base_ou_id(self) -> str:
        """Get the manually configured current base OU ID set in the Django admin panel."""
        for policy in AWSPolicy.objects.all():
            if policy.is_current_policy:
                return policy.base_ou_id
        raise Exception("No current base OU ID found")

    def get_current_policy_id(self) -> str:
        """Get the manually configured current policy ID set in the Django admin panel."""
        for policy in AWSPolicy.objects.all():
            if policy.is_current_policy:
                return policy.policy_id
        raise Exception("No current policy found")

    def get_current_policy_tag(self) -> dict:
        """Get the manually configured current policy tag set in the Django admin panel."""
        for policy in AWSPolicy.objects.all():
            if policy.is_current_policy:
                tag = {"Key": policy.tags_key}
                tag["Value"] = policy.tags_value if policy.tags_value else ""
                return tag
        raise Exception("No current policy tag found")

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
        accounts_created = 0
        accounts_moved = 0

        for new_member in new_member_accounts:
            response = self.api_talker.create_account(
                new_member.project_email, new_member.project_slug, [self.get_current_policy_tag()]
            )
            request_id = response["CreateAccountStatus"]["Id"]

            for _ in range(self.ACCOUNT_REQUEST_MAX_ATTEMPTS):
                time.sleep(self.ACCOUNT_REQUEST_INTERVAL_SECONDS)

                try:
                    response_status = self.api_talker.describe_create_account_status(request_id)
                except ClientError as error:
                    self.logger.debug(f"Failed to get status of account with e-mail: '{new_member.project_email}'.")
                    self.logger.debug(error)
                    break

                request_state = response_status["CreateAccountStatus"]["State"]

                if request_state == "SUCCEEDED":
                    account_id = response_status["CreateAccountStatus"]["AccountId"]
                    self.logger.info(f"Created member account '{new_member.project_email}' with ID '{account_id}'.")
                    accounts_created += 1

                    try:
                        self.api_talker.move_account(account_id, root_id, destination_ou_id)
                        accounts_moved += 1
                        self.logger.info(f"Moved new member account '{new_member.project_email}'.")
                        self.api_talker.untag_resource(account_id, [self.get_current_policy_tag()["Key"]])
                    except ClientError as error:
                        self.logger.debug(f"Failed to move new member account '{new_member.project_email}'.")
                        self.logger.debug(error)
                    break

                elif request_state == "FAILED":
                    failure_reason = response_status["CreateAccountStatus"]["FailureReason"]
                    self.logger.debug(
                        f"Failed to create account with e-mail: {new_member.project_email}. "
                        f"Failure reason: {failure_reason}"
                    )
                    break

        accounts_to_create = len(new_member_accounts)
        self.logger.info(f"Accounts created: {accounts_created}/{accounts_to_create}")
        self.logger.info(f"Accounts moved:   {accounts_moved}/{accounts_to_create}")
        success = accounts_to_create == accounts_created == accounts_moved

        return success

    def pipeline(self) -> bool:
        """
        Single pipeline that integrates all buildings blocks for the AWS integration process.

        :return: True iff all pipeline stages successfully executed.
        """
        base_ou_id = self.get_current_base_ou_id()
        policy_id = self.get_current_policy_id()
        root_id = self.api_talker.list_roots()[0]["Id"]

        aws_tree = self.extract_aws_setup(base_ou_id)
        self.checker.check_double_iteration_names(aws_tree)

        aws_sync_data = aws_tree.awstree_to_syncdata_list()
        giphouse_sync_data = self.get_syncdata_from_giphouse()
        merged_sync_data = self.generate_aws_sync_list(giphouse_sync_data, aws_sync_data)

        course_ou_id = self.get_or_create_course_ou(aws_tree)
        self.attach_policy(course_ou_id, policy_id)

        return self.create_and_move_accounts(merged_sync_data, root_id, course_ou_id)

    def synchronise(self, request):
        """
        Synchronise projects of the current semester to AWS and notify user of success or potential errors.

        :param request: HTTP request indicating the synchronization button has been pressed.
        """
        try:
            synchronisation_success = self.pipeline()

            if synchronisation_success:
                messages.success(request, self.SUCCESS_MSG)
            else:
                messages.warning(request, self.FAIL_MSG)
        except ClientError as api_error:
            messages.error(request, self.API_ERROR_MSG)
            self.logger.error(api_error)
        except Exception as sync_error:
            messages.error(request, self.SYNC_ERROR_MSG)
            self.logger.error(sync_error)
