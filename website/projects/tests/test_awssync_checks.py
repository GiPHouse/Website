"""Tests for awssync/checks.py."""

from django.test import TestCase

from projects.awssync_checks import Checks
from projects.awssync_structs import AWSTree, Iteration, SyncData


class ChecksTest(TestCase):
    def setUp(self):
        self.checks = Checks()
        self.aws_tree1 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Spring 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree2 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Fall 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree3 = AWSTree(
            "AWS Tree",
            "12345",
            [
                Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        SyncData("email1@example.com", "project1", "Fall 2020"),
                        SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                Iteration(
                    "Fall 2020",
                    "98765",
                    [
                        SyncData("email3@example.com", "project3", "Fall 2021"),
                        SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

    def test_check_members_in_correct_iteration(self):
        # Test when correct
        self.assertIsNone(self.checks.check_members_in_correct_iteration(self.aws_tree1))

        # Test when incorrect
        self.assertRaises(Exception, self.checks.check_members_in_correct_iteration, self.aws_tree2)

    def test_check_double_iteration_names(self):
        # Test when correct
        self.assertIsNone(self.checks.check_double_iteration_names(self.aws_tree1))

        # Test when double
        self.assertRaises(Exception, self.checks.check_double_iteration_names, self.aws_tree3)
