"""Tests for awssync_refactored.py."""
import json
from unittest.mock import patch

from botocore.exceptions import ClientError

from django.test import TestCase

from moto import mock_organizations

from courses.models import Semester

from projects.aws.awssync_refactored import AWSSyncRefactored
from projects.aws.awssync_structs import AWSTree, Iteration, SyncData


@mock_organizations
class AWSSyncRefactoredTest(TestCase):
    def setUp(self):
        self.sync = AWSSyncRefactored()

    def test_get_or_create_course_ou__new(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]
        tree = AWSTree("root", root_id, [])
        current_semester_name = "Spring 2023"

        with patch.object(Semester.objects, "get_or_create_current_semester", return_value=current_semester_name):
            course_ou_id = self.sync.get_or_create_course_ou(tree)

        course_ou_exists = any(
            ou["Id"] == course_ou_id and ou["Name"] == current_semester_name
            for ou in self.sync.api_talker.list_organizational_units_for_parent(root_id)
        )

        self.assertTrue(course_ou_exists)

    def test_get_or_create_course_ou__already_exists(self):
        tree = AWSTree(
            "root",
            "r-123",
            [
                Iteration("Spring 2023", "ou-456", [SyncData("alice@giphouse.nl", "alices-project", "Spring 2023")]),
                Iteration("Fall 2023", "ou-789", [SyncData("bob@giphouse.nl", "bobs-project", "Fall 2023")]),
            ],
        )

        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2023"):
            course_ou_id = self.sync.get_or_create_course_ou(tree)
        self.assertEqual("ou-456", course_ou_id)

    def test_attach_policy__not_attached(self):
        self.sync.api_talker.create_organization(feature_set="ALL")
        root_id = self.sync.api_talker.list_roots()[0]["Id"]

        new_policy_content = json.dumps(
            {"Version": "2012-10-17", "Statement": [{"Effect": "Deny", "Action": "*", "Resource": "*"}]}
        )
        new_policy_id = self.sync.api_talker.org_client.create_policy(
            Content=new_policy_content, Description="Deny all access.", Name="DenyAll", Type="SERVICE_CONTROL_POLICY"
        )["Policy"]["PolicySummary"]["Id"]

        self.sync.attach_policy(root_id, new_policy_id)
        attached_policies = self.sync.api_talker.org_client.list_policies_for_target(
            TargetId=root_id, Filter="SERVICE_CONTROL_POLICY"
        )["Policies"]
        attached_policy_ids = [policy["Id"] for policy in attached_policies]

        self.assertIn(new_policy_id, attached_policy_ids)

    def test_attach_policy__caught_exception(self):
        # Error code "DuplicatePolicyAttachmentException" can not be simulated by moto, so it is mocked.
        attach_policy_hard_side_effect = ClientError(
            {"Error": {"Code": "DuplicatePolicyAttachmentException"}}, "attach_policy"
        )
        with patch.object(
            self.sync.api_talker.org_client, "attach_policy", side_effect=attach_policy_hard_side_effect
        ):
            return_value = self.sync.attach_policy("r-123", "p-123")

        self.assertIsNone(return_value)

    def test_attach_policy__reraised_exception(self):
        self.assertRaises(ClientError, self.sync.attach_policy, "r-123", "p-123")
