from __future__ import annotations

import logging

from botocore.exceptions import ClientError

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.aws.awsapitalker import AWSAPITalker
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData
from projects.models import Project


class AWSSyncRefactored:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.api_talker = AWSAPITalker()
        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)
        self.fail = False

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
