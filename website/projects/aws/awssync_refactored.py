from __future__ import annotations

import logging

from botocore.exceptions import ClientError

from courses.models import Semester

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_checks import Checks
from projects.aws.awssync_checks_permissions import api_permissions
from projects.aws.awssync_structs import AWSTree


class AWSSyncRefactored:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()
        self.logger = logging.getLogger("django.aws")
        self.fail = False

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

    def pipeline(self) -> bool:
        """
        Single pipeline that integrates all buildings blocks for the AWS integration process.

        :return: True iff all pipeline stages successfully executed.
        """
        self.ensure_organization_created()
        root_id = self.api_talker.list_roots()[0]["Id"]

        checker = Checks()
        checker.pipeline_preconditions(api_permissions)

        # TODO refactor according to refactored extract_aws_setup
        aws_tree = self.extract_aws_setup(root_id)
        if self.fail:
            self.logger.debug("Extracting AWS setup failed.")
            return False

        aws_sync_data = aws_tree.awstree_to_syncdata_list()
        # TODO refactor according to refactored get_emails_with_teamids, generate_aws_sync_list
        giphouse_sync_data = self.get_emails_with_teamids()
        merged_sync_data = self.generate_aws_sync_list(giphouse_sync_data, aws_sync_data)

        checker.check_members_in_correct_iteration(aws_tree)
        checker.check_double_iteration_names(aws_tree)

        ou_id = self.get_or_create_course_ou(aws_tree)

        # TODO change hardcoded policy id to environment variable
        policy_id = "hardcoded_policy_id"
        self.attach_policy(ou_id, policy_id)

        # TODO refactor according to refactored pipeline_create_and_move_accounts
        if not self.pipeline_create_and_move_accounts(merged_sync_data, root_id, ou_id):
            return False

        return True

    def success_message(success: bool):
        """
        Print a message to the screen which notifies user whether synchronization succeeded or not.

        :param success: whether synchronization was successful or not.
        """
        # TODO integrate error box task

    def synchronise(self):
        """Synchronise projects of the current semester to AWS and notify user of success or potential errors."""
        try:
            synchronization_success = self.pipeline()
        # TODO extend error handling
        except ClientError as aws_error:
            self.logger.debug("An AWS API call caused an error.")
            synchronization_success = False
        except Exception as sync_error:
            self.logger.debug("Something went wrong while synchronizing with AWS.")
            synchronization_success = False

        self.success_message(synchronization_success)
