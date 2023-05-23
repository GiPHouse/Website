from __future__ import annotations

import logging
import time

from botocore.exceptions import ClientError

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_checks import Checks
from projects.aws.awssync_checks_permissions import api_permissions
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData
from projects.models import Project


class AWSSyncRefactored:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()
        self.checker = Checks()
        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)
        self.fail = False

        self.ACCOUNT_REQUEST_INTERVAL_SECONDS = 5
        self.ACCOUNT_REQUEST_MAX_ATTEMPTS = 3

        self.accounts_created = 0
        self.accounts_moved = 0

    def get_syncdata_from_giphouse(self) -> list[SyncData]:
        """
        Create a list of SyncData struct containing email, slug and semester.

        Slug and semester combined are together an uniqueness constraint.

        :return: list of SyncData structs with email, slug and semester
        """
        sync_data_list = []
        current_semester = Semester.objects.get_or_create_current_semester()

        for project in Project.objects.filter(mailinglist__isnull=False, semester=current_semester).values(
            "slug", "semester", "mailinglist"
        ):
            project_slug = project["slug"]
            project_semester = str(Semester.objects.get(pk=project["semester"]))
            project_email = MailingList.objects.get(pk=project["mailinglist"]).email_address

            sync_data = SyncData(project_email, project_slug, project_semester)
            sync_data_list.append(sync_data)
        return sync_data_list

    def generate_aws_sync_list(self, giphouse_data: list[SyncData], aws_data: list[SyncData]) -> list[SyncData]:
        """
        Generate the list of users that are registered on the GiPhouse website, but are not yet invited for AWS.

        This includes their ID and email address, to be able to put users in the correct AWS organization later.
        """
        return [project for project in giphouse_data if project not in aws_data]

    def get_tag_value(self, tags: list[dict[str, str]], key: str) -> str:
        """Return the value of the tag with the given key, or None if no such tag exists."""
        for tag in tags:
            if tag["Key"] == key:
                return tag["Value"]
        return None

    def extract_aws_setup(self, parent_ou_id: str) -> AWSTree:
        """
        Give a list of all the children of the parent OU.

        :param parent_ou_id: The ID of the parent OU.
        :return: A AWSTree object containing all the children of the parent OU.
        """
        member_accounts = []
        aws_tree = AWSTree(
            "root",
            parent_ou_id,
            [
                Iteration(
                    ou["Name"],
                    ou["Id"],
                    member_accounts := [
                        SyncData(
                            account["Email"],
                            self.get_tag_value(tags, "project_slug"),
                            self.get_tag_value(tags, "project_semester"),
                        )
                        for account in self.api_talker.list_accounts_for_parent(parent_id=ou["Id"])
                        for tags in [self.api_talker.list_tags_for_resource(resource_id=account["Id"])]
                    ],
                )
                for ou in self.api_talker.list_organizational_units_for_parent(parent_id=parent_ou_id)
            ],
        )

        incomplete_accounts = [
            account for account in member_accounts if not (account.project_slug and account.project_semester)
        ]

        if incomplete_accounts:
            raise Exception(f"Found incomplete accounts in AWS: {incomplete_accounts}.")

        return aws_tree

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

    def ensure_organization_created(self):
        """Create an organization if it does not yet exist."""
        try:
            self.api_talker.create_organization("ALL")
        except ClientError as error:
            if error.response["Error"]["Code"] != "AlreadyInOrganizationException":
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

                    self.accounts_created += 1
                    try:
                        self.api_talker.move_account(account_id, root_id, destination_ou_id)
                        self.accounts_moved += 1
                    except ClientError as error:
                        self.logger.debug(f"Failed to move account with e-mail: {new_member.project_email}.")
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
        success = accounts_to_create == self.accounts_created == self.accounts_moved
        return success

    def pipeline(self) -> bool:
        """
        Single pipeline that integrates all buildings blocks for the AWS integration process.

        :return: True iff all pipeline stages successfully executed.
        """
        self.ensure_organization_created()
        root_id = self.api_talker.list_roots()[0]["Id"]
        self.checker.pipeline_preconditions(api_permissions)

        aws_tree = self.extract_aws_setup(root_id)
        self.checker.check_members_in_correct_iteration(aws_tree)
        self.checker.check_double_iteration_names(aws_tree)

        aws_sync_data = aws_tree.awstree_to_syncdata_list()
        giphouse_sync_data = self.get_syncdata_from_giphouse()
        merged_sync_data = self.generate_aws_sync_list(giphouse_sync_data, aws_sync_data)

        ou_id = self.get_or_create_course_ou(aws_tree)

        # TODO change hardcoded policy id to environment variable
        policy_id = "p-jkrnoldh"
        self.attach_policy(ou_id, policy_id)

        return self.create_and_move_accounts(merged_sync_data, root_id, ou_id)

    def success_message(self, success: bool):
        """
        Print a message to the screen which notifies user whether synchronisation succeeded or not.

        :param success: whether synchronisation was successful or not.
        """
        self.logger.debug(f"pipeline success: {success}")
        # TODO integrate error box task

    def synchronise(self):
        """
        Synchronise projects of the current semester to AWS and notify user of success or potential errors.

        return: whether synchronisation was successful or not.
        """
        try:
            synchronisation_success = self.pipeline()
            self.logger.debug(f"Accounts created: {self.accounts_created}")
            self.logger.debug(f"Accounts moved: {self.accounts_moved}")
        # TODO extend error handling
        except ClientError as aws_error:
            self.logger.debug("An AWS API call caused an error.")
            self.logger.debug(aws_error)
            synchronisation_success = False
        except Exception as sync_error:
            self.logger.debug("Something went wrong while synchronising with AWS.")
            self.logger.debug(sync_error)
            synchronisation_success = False

        self.success_message(synchronisation_success)
        return synchronisation_success
