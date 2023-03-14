"""Framework for synchronisation with Amazon Web Services (AWS)."""

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


class AWSSync:
    """Synchronise with Amazon Web Services."""

    def __init__(self):
        """Create an AWSSync instance."""
        self.logger = logging.getLogger("django.aws")
        self.logger.setLevel(logging.DEBUG)
        self.org_info = None
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

    def generate_aws_sync_list(self, giphouse_data, aws_data):
        """
        Generate the list of users that are registered on the GiPhouse website, but are not yet invited for AWS.

        This includes their ID and email address, to be able to put users in the correct AWS orginization later.
        """
        sync_list = [x for x in giphouse_data if x not in aws_data]
        return sync_list
