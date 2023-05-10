"""Tests for awssync_structs.py."""

from unittest.mock import patch

from django.test import TestCase

from courses.models import Semester

from projects.aws import awssync


class SyncDataTest(TestCase):
    """Test SyncData class (struct)."""

    def setUp(self):
        """setup test environment."""
        self.sync = awssync.SyncData

    def test_throw_type_error_SyncData_class(self):
        """Test Type Error when equals is called on wrong type."""
        self.assertRaises(TypeError, self.sync("a", "b", "c").__eq__, 123)


class AWSSyncListTest(TestCase):
    """Test AWSSyncList class."""

    def setUp(self):
        self.sync = awssync.AWSSync()
        self.syncData = awssync.SyncData

        self.test1 = self.syncData("test1@test1.test1", "test1", "test1")
        self.test2 = self.syncData("test2@test2.test2", "test2", "test2")
        self.test3 = self.syncData("test3@test3.test3", "test3", "test3")

    def test_AWS_sync_list_both_empty(self):
        gip_list = []
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_empty_AWS(self):
        gip_list = [self.test1, self.test2]
        aws_list = []
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), gip_list)

    def test_AWS_sync_list_empty_GiP(self):
        gip_list = []
        aws_list = [self.test1, self.test2]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [])

    def test_AWS_sync_list_both_full(self):
        gip_list = [self.test1, self.test2]
        aws_list = [self.test2, self.test3]
        self.assertEquals(self.sync.generate_aws_sync_list(gip_list, aws_list), [self.test1])


class AWSTreeChecksTest(TestCase):
    """Test checks done on AWSTree data struncture."""

    def setUp(self):
        self.sync = awssync.AWSSync()
        self.awstree = awssync.AWSTree("Name", "1234", [])
        self.iteration = awssync.Iteration("Name", "1234", [])
        self.sync_data = awssync.SyncData("email@example.com", "Project X", "Spring 2020")

        self.sync_list = [
            awssync.SyncData("email1@example.com", "Spring 2022", "Project A"),
            awssync.SyncData("email2@example.com", "Fall 2022", "Project B"),
            awssync.SyncData("email3@example.com", "Spring 2022", "Project C"),
        ]
        self.aws_list = [
            awssync.SyncData("email4@example.com", "Fall 2021", "Project D"),
            awssync.SyncData("email5@example.com", "Spring 2022", "Project E"),
            awssync.SyncData("email6@example.com", "Fall 2022", "Project F"),
        ]

        self.treelist = [
            awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
            awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
            awssync.SyncData("email3@example.com", "project3", "Spring 2021"),
            awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
        ]

        self.aws_tree1 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Spring 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree2 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Spring 2021",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Fall 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

        self.aws_tree3 = awssync.AWSTree(
            "AWS Tree",
            "12345",
            [
                awssync.Iteration(
                    "Fall 2020",
                    "54321",
                    [
                        awssync.SyncData("email1@example.com", "project1", "Fall 2020"),
                        awssync.SyncData("email2@example.com", "project2", "Fall 2020"),
                    ],
                ),
                awssync.Iteration(
                    "Fall 2020",
                    "98765",
                    [
                        awssync.SyncData("email3@example.com", "project3", "Fall 2021"),
                        awssync.SyncData("email4@example.com", "project4", "Spring 2021"),
                    ],
                ),
            ],
        )

    def test_repr_AWSTree(self):
        self.assertEquals(repr(self.awstree), "AWSTree('Name', '1234', [])")

    def test_repr_Iteration(self):
        self.assertEquals(repr(self.iteration), "Iteration('Name', '1234', [])")

    def test_repr_SyncData(self):
        self.assertEquals(repr(self.sync_data), "SyncData('email@example.com', 'Project X', 'Spring 2020')")

    def test_awstree_to_syncdata_list(self):
        self.assertEqual(self.aws_tree1.awstree_to_syncdata_list(), self.treelist)

    def test_check_for_double_member_email(self):
        # Test when there are no duplicate emails
        self.assertFalse(self.sync.check_for_double_member_email(self.aws_list, self.sync_list))

        # Test when there is a duplicate email
        self.sync_list.append(awssync.SyncData("email4@example.com", "Spring 2022", "Project G"))
        self.assertTrue(self.sync.check_for_double_member_email(self.aws_list, self.sync_list))

    def test_check_current_ou_exists(self):
        # Test when current semester OU does not exist
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Fall 2022"):
            self.assertTrue(Semester.objects.get_or_create_current_semester() == "Fall 2022")
            val1, val2 = self.sync.check_current_ou_exists(self.aws_tree1)
            self.assertEqual((val1, val2), (False, None))

        # Test when current semester OU exists
        with patch.object(Semester.objects, "get_or_create_current_semester", return_value="Spring 2021"):
            self.assertTrue(Semester.objects.get_or_create_current_semester() == "Spring 2021")
            val1, val2 = self.sync.check_current_ou_exists(self.aws_tree1)
            self.assertEqual((val1, val2), (True, "98765"))

    def test_AWSTree_equals(self):
        self.assertEqual(self.aws_tree1, self.aws_tree1)
        self.assertNotEqual(self.aws_tree1, self.aws_tree2)
        self.assertRaises(TypeError, awssync.AWSTree("", "", []).__eq__, [])

    def test_Iteration_equals(self):
        self.assertEqual(self.aws_tree1.iterations[0], self.aws_tree1.iterations[0])
        self.assertNotEqual(self.aws_tree1.iterations[0], self.aws_tree1.iterations[1])
        self.assertRaises(TypeError, awssync.Iteration("", "", []).__eq__, [])
