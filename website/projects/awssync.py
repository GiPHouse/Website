"""Framework for synchronisation with Amazon Web Services (AWS)."""
from __future__ import annotations

import json
import logging

import boto3

from botocore.exceptions import ClientError

from courses.models import Semester

from mailing_lists.models import MailingList

from projects.models import Project


class SyncData:
    """Structure for AWS giphouse sync data."""

    def __init__(self, project_email, project_slug, project_semester):
        """Create SyncData instance."""
        self.project_email = project_email
        self.project_slug = project_slug
        self.project_semester = project_semester

    def __eq__(self, other):
        """Overload equals for SyncData type."""
        if not isinstance(other, SyncData):
            raise TypeError("Must compare to object of type SyncData")
        return (
            self.project_email == other.project_email
            and self.project_slug == other.project_slug
            and self.project_semester == other.project_semester
        )

    def __repr__(self):
        """Overload to string function for SyncData type."""
        return f"SyncData('{self.project_email}', '{self.project_slug}', '{self.project_semester}')"


class Iteration:
    """Datatype for AWS data in the Course iteration OU."""

    def __init__(self, name, ou_id, members: list[SyncData]):
        """Initialize Iteration object."""
        self.name = name
        self.ou_id = ou_id
        self.members = members

    def __repr__(self):
        """Overload to string function for Iteration datatype."""
        return f"Iteration('{self.name}', '{self.ou_id}', {self.members})"

    def __eq__(self, other: Iteration) -> bool:
        """Overload equals operator for Iteration objects."""
        if not isinstance(other, Iteration):
            raise TypeError("Must compare to object of type Iteration")
        return self.name == other.name and self.ou_id == other.ou_id and self.members == other.members


class AWSTree:
    """Tree structure for AWS data."""

    def __init__(self, name, ou_id, iterations: list[Iteration]):
        """Initialize AWSTree object."""
        self.name = name
        self.ou_id = ou_id
        self.iterations = iterations

    def __repr__(self):
        """Overload to string function for AWSTree object."""
        return f"AWSTree('{self.name}', '{self.ou_id}', {self.iterations})"

    def __eq__(self, other: AWSTree) -> bool:
        """Overload equals operator for AWSTree objects."""
        if not isinstance(other, AWSTree):
            raise TypeError("Must compare to object of type AWSTree")
        return self.name == other.name and self.ou_id == other.ou_id and self.iterations == other.iterations

    def awstree_to_syncdata_list(self):
        """Convert AWSTree to list of SyncData elements."""
        awslist = []

        for iteration in self.iterations:
            for member in iteration.members:
                awslist.append(member)

        return awslist


class AWSSync:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)
        self.org_info = None
        self.iterationOU_info = None
        self.fail = False
        self.logger.info("Created AWSSync instance.")

    def button_pressed(self):
        """
        Print debug message to show that the button has been pressed.

        :return: True if function executes successfully
        """
        self.logger.info("Pressed button")
        self.logger.info(self.get_emails_with_teamids())
        return True

    def get_all_mailing_lists(self):
        """
        Get all mailing lists from the database.

        :return: List of mailing lists
        """
        mailing_lists = MailingList.objects.all()
        mailing_list_names = [ml.email_address for ml in mailing_lists]
        return mailing_list_names

    def get_emails_with_teamids(self):
        """
        Create a list of SyncData struct containing email, slug and semester.

        Slug and semester combined are together an uniqueness constraint.

        :return: list of SyncData structs with email, slug and semester
        """
        email_ids = []

        for project in (
            Project.objects.filter(mailinglist__isnull=False)
            .filter(semester=Semester.objects.get_or_create_current_semester())
            .values("slug", "semester", "mailinglist")
        ):
            project_slug = project["slug"]
            project_semester = str(Semester.objects.get(pk=project["semester"]))
            project_email = MailingList.objects.get(pk=project["mailinglist"]).email_address

            sync_data = SyncData(project_email, project_slug, project_semester)
            email_ids.append(sync_data)
        return email_ids

    def create_aws_organization(self):
        """Create an AWS organization with the current user as the management account."""
        client = boto3.client("organizations")
        try:
            response = client.create_organization(FeatureSet="ALL")
            self.org_info = response["Organization"]
            self.logger.info("Created an AWS organization and saved organization info.")
        except ClientError as error:
            self.fail = True
            self.logger.error("Something went wrong creating an AWS organization.")
            self.logger.debug(f"{error}")
            self.logger.debug(f"{error.response}")

    def create_course_iteration_OU(self, iteration_id):
        """
        Create an OU for the course iteration.

        :param iteration_id: The ID of the course iteration

        :return: The ID of the OU
        """
        client = boto3.client("organizations")
        if self.org_info is None:
            self.logger.info("No organization info found. Creating an AWS organization.")
            self.fail = True
        else:
            try:
                response = client.create_organizational_unit(
                    ParentId=self.org_info["Id"],
                    Name=f"Course Iteration {iteration_id}",
                )
                self.logger.info(f"Created an OU for course iteration {iteration_id}.")
                self.iterationOU_info = response["OrganizationalUnit"]
                return response["OrganizationalUnit"]["Id"]
            except ClientError as error:
                self.fail = True
                self.logger.error(f"Something went wrong creating an OU for course iteration {iteration_id}.")
                self.logger.debug(f"{error}")
                self.logger.debug(f"{error.response}")

    def generate_aws_sync_list(self, giphouse_data: list[SyncData], aws_data: list[SyncData]):
        """
        Generate the list of users that are registered on the GiPhouse website, but are not yet invited for AWS.

        This includes their ID and email address, to be able to put users in the correct AWS orginization later.
        """
        sync_list = [x for x in giphouse_data if x not in aws_data]
        return sync_list

    def create_scp_policy(self, policy_name, policy_description, policy_content):
        """
        Create a SCP policy.

        :param policy_name: The policy name.
        :param policy_description: The policy description.
        :param policy_content: The policy configuration as a dictionary. The policy is automatically
                               converted to JSON format, including escaped quotation marks.
        :return: Details of newly created policy as a dict on success and NoneType object otherwise.
        """
        client = boto3.client("organizations")
        try:
            response = client.create_policy(
                Content=json.dumps(policy_content),
                Description=policy_description,
                Name=policy_name,
                Type="SERVICE_CONTROL_POLICY",
            )
        except ClientError as error:
            self.fail = True
            self.logger.error("Something went wrong creating an SCP policy.")
            self.logger.error(error)
        else:
            return response["Policy"]

    def attach_scp_policy(self, policy_id, target_id):
        """
        Attaches a SCP policy to a target (root, OU, or member account).

        :param policy_id: The ID of the policy to be attached.
        :param target_id: The ID of the target root, OU, or member account.
        """
        client = boto3.client("organizations")
        try:
            client.attach_policy(PolicyId=policy_id, TargetId=target_id)
        except ClientError as error:
            self.fail = True
            self.logger.error("Something went wrong attaching an SCP policy to a target.")
            self.logger.debug(f"{error}")
            self.logger.debug(f"{error.response}")

    # TODO: check if this function is really needed

    def check_for_double_member_email(self, aws_list: list[SyncData], sync_list: list[SyncData]):
        """Check if no users are assigned to multiple projects."""
        sync_emails = [x.project_email for x in sync_list]
        aws_emails = [x.project_email for x in aws_list]

        duplicates = [email for email in sync_emails if email in aws_emails]

        for duplicate in duplicates:
            error = f"Email address {duplicate} is already in the list of members in AWS"
            self.logger.info("An email clash occured while syncing.")
            self.logger.debug(error)

        if duplicates != []:
            return True
        return False

    def check_current_ou_exists(self, AWSdata: AWSTree):
        """
        Check if the the OU (organizational unit) for the current semester already exists in AWS.

        Get data in tree structure (dictionary) defined in the function that retrieves the AWS data
        """
        current = Semester.objects.get_or_create_current_semester()

        for iteration in AWSdata.iterations:
            if current == iteration.name:
                return (True, iteration.ou_id)

        return (False, None)

    # TODO: Do we want to check for this?
    def check_members_in_correct_iteration(self, AWSdata: AWSTree):
        """Check if the data from the member tag matches the semester OU it is in."""
        incorrect_emails = []
        for iteration in AWSdata.iterations:
            for member in iteration.members:
                if member.project_semester != iteration.name:
                    incorrect_emails.append(member.project_email)

        if incorrect_emails != []:
            return (False, incorrect_emails)

        return (True, None)

    def check_double_iteration_names(self, AWSdata: AWSTree):
        """Check if there are multiple OU's with the same name in AWS."""
        names = [iteration.name for iteration in AWSdata.iterations]
        doubles = []

        for name in names:
            if names.count(name) != 1 and name not in doubles:
                doubles.append(name)

        if doubles != []:
            return (True, doubles)
        return (False, None)
