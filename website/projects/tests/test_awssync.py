"""Tests for awssync.py."""

from unittest.mock import patch

import boto3

from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_organizations

from courses.models import Semester

from mailing_lists.models import MailingList

from projects import awssync
from projects.models import Project


class SyncDataTest(TestCase):
    """Test SyncData class (struct)."""

    def setUp(self):
        """setup test environment."""
        self.sync = awssync.SyncData

    def test_throw_type_error_SyncData_class(self):
        """Test Type Error when equals is called on wrong type."""
        with self.assertRaises(TypeError) as context:
            self.sync("", "", "") == []
        self.assertTrue("Must compare to object of type SyncData" in str(context.exception))


class AWSSyncTest(TestCase):
    """Test AWSSync class."""

    def setUp(self):
        """Set up testing environment."""
        self.sync = awssync.AWSSync()
        self.semester = Semester.objects.create(year=2023, season=Semester.SPRING)
        self.mailing_list = MailingList.objects.create(address="test1")
        self.project = Project.objects.create(id=1, name="test1", semester=self.semester, slug="test1")
        self.mailing_list.projects.add(self.project)

    def test_button_pressed(self):
        """Test button_pressed function."""
        return_value = self.sync.button_pressed()
        self.assertTrue(return_value)

    def test_get_all_mailing_lists(self):
        """Test get_all_mailing_lists function."""
        mailing_lists = self.sync.get_all_mailing_lists()
        self.assertIsInstance(mailing_lists, list)

    def test_get_emails_with_teamids_normal(self):
        """Test get_emails_with_teamids function."""
        email_id = self.sync.get_emails_with_teamids()

        self.assertIsInstance(email_id, list)
        self.assertIsInstance(email_id[0], awssync.SyncData)
        expected_result = [awssync.SyncData("test1@giphouse.nl", "test1", "Spring 2023")]
        self.assertEqual(email_id, expected_result)

    def test_get_emails_with_teamids_no_project(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        self.mailing_list = MailingList.objects.create(address="test2")
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_emails_with_teamids_no_mailing_list(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        Project.objects.all().delete()
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def test_get_emails_with_teamids_different_semester(self):
        """Test get_emails_with_teamids function."""
        MailingList.objects.all().delete()
        new_semester = Semester.objects.create(year=2022, season=Semester.FALL)
        self.mailing_list = MailingList.objects.create(address="test2")
        self.project = Project.objects.create(id=2, name="test2", semester=new_semester, slug="test2")
        self.mailing_list.projects.add(self.project)
        email_id = self.sync.get_emails_with_teamids()
        self.assertIsInstance(email_id, list)
        self.assertEqual(email_id, [])

    def mock_api(self, operation_name, kwarg):
        if operation_name == "CreateOrganization":
            raise ClientError(
                {
                    "Error": {
                        "Message": "The AWS account is already a member of an organization.",
                        "Code": "AlreadyInOrganizationException",
                    },
                    "ResponseMetadata": {
                        "RequestId": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                        "HTTPStatusCode": 400,
                        "HTTPHeaders": {
                            "x-amzn-requestid": "ffffffff-ffff-ffff-ffff-ffffffffffff",
                            "content-type": "application/x-amz-json-1.1",
                            "content-length": "111",
                            "date": "Sun, 01 Jan 2023 00:00:00 GMT",
                            "connection": "close",
                        },
                        "RetryAttempts": 0,
                    },
                    "Message": "The AWS account is already a member of an organization.",
                },
                "create_organization",
            )

    @mock_organizations
    def test_create_aws_organization(self):
        moto_client = boto3.client("organizations")
        org = self.sync
        org.create_aws_organization()
        describe_org = moto_client.describe_organization()["Organization"]
        self.assertEqual(describe_org, org.org_info)

    @patch("botocore.client.BaseClient._make_api_call", mock_api)
    def test_create_aws_organization__exception(self):
        org = self.sync
        org.create_aws_organization()
        self.assertTrue(org.fail)
        self.assertIsNone(org.org_info)
