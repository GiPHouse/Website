"""
Test for the GSuite sync in the mailing lists package

This code is based on concrexit by the techinci of svthalia.
Copyright (C) 2020 Technicie svthalia

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import MagicMock, patch

from django.conf import settings
from django.test import TestCase
from django.urls import reverse

from googleapiclient.errors import HttpError

from httplib2 import Response

from mailing_lists import gsuite
from mailing_lists.gsuite import GSuiteSyncService, MemoryCache
from mailing_lists.models import ExtraEmailAddress, MailingList, MailingListAlias

from tasks.models import Task


def assert_not_called_with(self, *args, **kwargs):
    try:
        self.assert_any_call(*args, **kwargs)
    except AssertionError:
        return


MagicMock.assert_not_called_with = assert_not_called_with


class MemoryCacheTestCase(TestCase):
    def test_memory_cache(self):
        mc = MemoryCache()

        mc.set("url", "content")

        self.assertEqual(mc.get("url"), "content")


class GSuiteSyncTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.settings_api = MagicMock()
        cls.directory_api = MagicMock()
        cls.logger_mock = MagicMock()
        gsuite.logger = cls.logger_mock

        cls.sync_service = GSuiteSyncService(groups_settings_api=cls.settings_api, directory_api=cls.directory_api)
        cls.mailing_list = MailingList.objects.create(address="new_group", description="some description")
        MailingList.objects.create(address="archive", archive_instead_of_delete=True).delete()
        MailingList.objects.create(address="delete", archive_instead_of_delete=False).delete()
        MailingListAlias.objects.create(mailing_list=cls.mailing_list, address="alias2")
        ExtraEmailAddress.objects.create(mailing_list=cls.mailing_list, address=f"test2@{settings.GSUITE_DOMAIN}")

    def setUp(self):
        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    @patch("mailing_lists.gsuite.build")
    def test_gsuite_init(self, build, from_service_account_info):
        from_service_account_info.return_value = MagicMock(return_value="creds")

        GSuiteSyncService()

        build.assert_called()
        from_service_account_info.assert_called()

    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    @patch("mailing_lists.gsuite.build")
    def test_gsuite_init_groupsettings(self, build, from_service_account_info):
        from_service_account_info.return_value = MagicMock(return_value="creds")

        GSuiteSyncService(groups_settings_api=MagicMock())

        build.assert_called()
        from_service_account_info.assert_called()

    @patch("google.oauth2.service_account.Credentials.from_service_account_info")
    @patch("mailing_lists.gsuite.build")
    def test_gsuite_init_directory(self, build, from_service_account_info):
        from_service_account_info.return_value = MagicMock(return_value="creds")

        GSuiteSyncService(directory_api=MagicMock())

        build.assert_called()
        from_service_account_info.assert_called()

    def test_gsuite_eq(self):
        self.assertFalse(
            GSuiteSyncService.GroupData(
                "new_group", "some description", ["alias1"], [f"test1@{settings.GSUITE_DOMAIN}"],
            )
            == 0
        )

        self.assertTrue(
            GSuiteSyncService.GroupData(
                "new_group", "some description", ["alias1"], [f"test1@{settings.GSUITE_DOMAIN}"],
            )
            == GSuiteSyncService.GroupData(
                "new_group", "some description", ["alias1"], [f"test1@{settings.GSUITE_DOMAIN}"],
            )
        )

        self.assertFalse(
            GSuiteSyncService.GroupData(
                "new_group", "some description", ["alias1"], [f"test1@{settings.GSUITE_DOMAIN}"],
            )
            == GSuiteSyncService.GroupData(
                "other_group", "some description", ["alias1"], [f"test1@{settings.GSUITE_DOMAIN}"],
            )
        )

    def test_get_all_lists(self):
        self.assertEqual(len(self.sync_service._get_all_lists()), 1)

    def test_get_lists_to_delete(self):
        self.assertEqual(self.sync_service._get_list_names_to_delete(), ["delete"])

    def test_get_lists_to_archive(self):
        self.assertEqual(self.sync_service._get_list_names_to_archive(), ["archive"])

    def test_mailing_list_to_group(self):
        group = GSuiteSyncService.mailing_list_to_group(self.mailing_list)
        self.assertEqual(
            group,
            GSuiteSyncService.GroupData(
                "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
            ),
        )

    def test_group_settings(self):
        self.assertEqual(
            self.sync_service._group_settings(),
            {
                "whoCanJoin": "INVITED_CAN_JOIN",
                "whoCanViewMembership": "ALL_MANAGERS_CAN_VIEW",
                "whoCanViewGroup": "ALL_MANAGERS_CAN_VIEW",
                "whoCanInvite": "ALL_MANAGERS_CAN_INVITE",
                "whoCanAdd": "ALL_MANAGERS_CAN_ADD",
                "allowExternalMembers": "true",
                "whoCanPostMessage": "ANYONE_CAN_POST",
                "allowWebPosting": "true",
                "maxMessageBytes": 26214400,
                "isArchived": "true",
                "archiveOnly": "false",
                "messageModerationLevel": "MODERATE_NONE",
                "spamModerationLevel": "MODERATE",
                "replyTo": "REPLY_TO_IGNORE",
                "customReplyTo": "",
                "includeCustomFooter": "false",
                "customFooterText": "",
                "sendMessageDenyNotification": "false",
                "defaultMessageDenyNotificationText": "",
                "showInGroupDirectory": "true",
                "allowGoogleCommunication": "false",
                "membersCanPostAsTheGroup": "false",
                "messageDisplayFont": "DEFAULT_FONT",
                "includeInGlobalAddressList": "true",
                "whoCanLeaveGroup": "ALL_MEMBERS_CAN_LEAVE",
                "whoCanContactOwner": "ALL_MANAGERS_CAN_CONTACT",
                "whoCanAddReferences": "NONE",
                "whoCanAssignTopics": "NONE",
                "whoCanUnassignTopic": "NONE",
                "whoCanTakeTopics": "NONE",
                "whoCanMarkDuplicate": "NONE",
                "whoCanMarkNoResponseNeeded": "NONE",
                "whoCanMarkFavoriteReplyOnAnyTopic": "NONE",
                "whoCanMarkFavoriteReplyOnOwnTopic": "NONE",
                "whoCanUnmarkFavoriteReplyOnAnyTopic": "NONE",
                "whoCanEnterFreeFormTags": "NONE",
                "whoCanModifyTagsAndCategories": "NONE",
                "favoriteRepliesOnTop": "true",
                "whoCanApproveMembers": "ALL_MANAGERS_CAN_APPROVE",
                "whoCanBanUsers": "OWNERS_AND_MANAGERS",
                "whoCanModifyMembers": "OWNERS_AND_MANAGERS",
                "whoCanApproveMessages": "OWNERS_AND_MANAGERS",
                "whoCanDeleteAnyPost": "OWNERS_AND_MANAGERS",
                "whoCanDeleteTopics": "OWNERS_AND_MANAGERS",
                "whoCanLockTopics": "OWNERS_AND_MANAGERS",
                "whoCanMoveTopicsIn": "OWNERS_AND_MANAGERS",
                "whoCanMoveTopicsOut": "OWNERS_AND_MANAGERS",
                "whoCanPostAnnouncements": "OWNERS_AND_MANAGERS",
                "whoCanHideAbuse": "NONE",
                "whoCanMakeTopicsSticky": "NONE",
                "whoCanModerateMembers": "OWNERS_AND_MANAGERS",
                "whoCanModerateContent": "OWNERS_AND_MANAGERS",
                "whoCanAssistContent": "NONE",
                "customRolesEnabledForSettingsToBeMerged": "false",
                "enableCollaborativeInbox": "false",
                "whoCanDiscoverGroup": "ALL_IN_DOMAIN_CAN_DISCOVER",
            },
        )

    @patch("mailing_lists.gsuite.sleep")
    def test_create_group(self, sleep):
        with self.subTest("Successful"):
            self.sync_service.create_group(
                GSuiteSyncService.GroupData(
                    "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
                )
            )

            self.directory_api.groups().insert.assert_called_once_with(
                body={
                    "email": f"new_group@{settings.GSUITE_DOMAIN}",
                    "name": "new_group",
                    "description": "some description",
                }
            )

            self.settings_api.groups().update.assert_called_once_with(
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}", body=self.sync_service._group_settings(),
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.directory_api.groups().insert().execute.side_effect = HttpError(Response({"status": 500}), bytes())

            self.sync_service.create_group(
                GSuiteSyncService.GroupData(
                    "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
                )
            )

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()
        self.directory_api.groups().insert().execute.reset_mock(side_effect=True)

        with self.subTest("> 64 second wait for insert"):
            self.settings_api.groups().update().execute.side_effect = HttpError(Response({"status": 500}), bytes())

            self.sync_service.create_group(
                GSuiteSyncService.GroupData(
                    "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
                )
            )

            self.settings_api.groups().update.assert_called()
            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

        self.settings_api.reset_mock()
        self.settings_api.groups().update().execute.reset_mock(side_effect=True)
        self.directory_api.reset_mock()

    def test_update_group(self):
        with self.subTest("Successful"):
            self.sync_service.update_group(
                "new_group",
                GSuiteSyncService.GroupData(
                    "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
                ),
            )

            self.directory_api.groups().update.assert_called_once_with(
                body={
                    "email": f"new_group@{settings.GSUITE_DOMAIN}",
                    "name": "new_group",
                    "description": "some description",
                },
                groupKey=f"new_group@{settings.GSUITE_DOMAIN}",
            )

            self.settings_api.groups().update.assert_called_once_with(
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}", body=self.sync_service._group_settings()
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.directory_api.groups().update().execute.side_effect = HttpError(Response({"status": 500}), bytes())

            self.sync_service.update_group(
                "new_group",
                GSuiteSyncService.GroupData(
                    "new_group", "some description", ["alias2"], [f"test2@{settings.GSUITE_DOMAIN}"],
                ),
            )

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

    def test_archive_group(self):
        with self.subTest("Successful"):
            success = self.sync_service.archive_group("new_group")
            self.assertTrue(success)

            self.settings_api.groups().patch.assert_called_once_with(
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
                groupUniqueId=f"new_group@{settings.GSUITE_DOMAIN}",
            )

            self.directory_api.members().list.assert_called()
            self.directory_api.groups().aliases().list.assert_called()

        self.settings_api.reset_mock()
        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.settings_api.groups().patch().execute.side_effect = HttpError(Response({"status": 500}), bytes())

            success = self.sync_service.archive_group("new_group")
            self.assertFalse(success)

            self.directory_api.members().list.assert_not_called()
            self.directory_api.groups().aliases().list.assert_not_called()

    def test_delete_group(self):
        with self.subTest("Successful"):
            success = self.sync_service.delete_group("new_group")
            self.assertTrue(success)
            self.directory_api.groups().delete.assert_called()

        self.directory_api.reset_mock()

        with self.subTest("Failure"):
            self.directory_api.groups().delete().execute.side_effect = HttpError(Response({"status": 500}), bytes())

            success = self.sync_service.delete_group("new_group")
            self.assertFalse(success)

    def test_update_group_aliases(self):
        with self.subTest("Error getting existing list"):
            self.directory_api.groups().aliases().list().execute.side_effect = HttpError(
                Response({"status": 500}), bytes()
            )
            self.sync_service._update_group_aliases(GSuiteSyncService.GroupData(name="update_group"))

        self.directory_api.reset_mock()

        with self.subTest("Successful with some errors"):
            group_data = GSuiteSyncService.GroupData(
                name="update_group", aliases=["not_synced", "not_synced_error", "already_synced"],
            )

            existing_aliases = [
                {"alias": f"deleteme@{settings.GSUITE_DOMAIN}"},
                {"alias": f"deleteme_error@{settings.GSUITE_DOMAIN}"},
                {"alias": f"already_synced@{settings.GSUITE_DOMAIN}"},
            ]

            self.directory_api.groups().aliases().list().execute.side_effect = [{"aliases": existing_aliases}]

            self.directory_api.groups().aliases().insert().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.directory_api.groups().aliases().delete().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.sync_service._update_group_aliases(group_data)

            self.directory_api.groups().aliases().insert.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                body={"alias": f"not_synced@{settings.GSUITE_DOMAIN}"},
            )

            self.directory_api.groups().aliases().delete.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}", alias=f"deleteme@{settings.GSUITE_DOMAIN}",
            )

    def test_update_group_members(self):
        with self.subTest("Error getting existing list"):
            self.directory_api.members().list().execute.side_effect = HttpError(Response({"status": 500}), bytes())
            self.sync_service._update_group_members(GSuiteSyncService.GroupData(name="update_group"))

        self.directory_api.reset_mock()

        with self.subTest("Successful with some errors"):
            group_data = GSuiteSyncService.GroupData(
                name="update_group",
                addresses=["not_synced@example.com", "not_synced_error@example.com", "already_synced@example.com"],
            )

            existing_aliases = [
                {"email": "deleteme@example.com", "role": "MEMBER"},
                {"email": "deleteme_error@example.com", "role": "MEMBER"},
                {"email": "already_synced@example.com", "role": "MEMBER"},
                {"email": "donotdelete@example.com", "role": "MANAGER"},
            ]

            self.directory_api.members().list().execute.side_effect = [
                {"members": existing_aliases[:1], "nextPageToken": "some_token"},
                {"members": existing_aliases[1:]},
            ]

            self.directory_api.members().insert().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.directory_api.members().delete().execute.side_effect = [
                "success",
                HttpError(Response({"status": 500}), bytes()),
            ]

            self.sync_service._update_group_members(group_data)

            self.directory_api.members().insert.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}",
                body={"email": "not_synced@example.com", "role": "MEMBER"},
            )

            self.directory_api.members().delete.assert_any_call(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}", memberKey="deleteme@example.com",
            )

            self.directory_api.members().delete.assert_not_called_with(
                groupKey=f"update_group@{settings.GSUITE_DOMAIN}", memberKey="donotdelete@example.com",
            )

    def test_sync_mailing_lists(self):
        original_create = self.sync_service.create_group
        original_update = self.sync_service.update_group
        original_archive = self.sync_service.archive_group
        original_delete = self.sync_service.delete_group
        original_get_all_lists = self.sync_service._get_all_lists

        self.sync_service.create_group = MagicMock()
        self.sync_service.update_group = MagicMock()
        self.sync_service.archive_group = MagicMock()
        self.sync_service.delete_group = MagicMock()
        self.sync_service._get_all_lists = MagicMock()
        self.sync_service._get_list_names_to_archive = MagicMock()
        self.sync_service._get_list_names_to_delete = MagicMock()

        with self.subTest("Error getting existing list"):
            self.directory_api.groups().list().execute.side_effect = HttpError(Response({"status": 500}), bytes())
            self.sync_service.sync_mailing_lists()

        self.directory_api.reset_mock()

        with self.subTest("Successful defaults without task"):
            self.sync_service.task = None
            existing_groups = [
                {"name": "delete_me", "directMembersCount": "3"},
                {"name": "already_synced", "directMembersCount": "2"},
                {"name": "ignore", "directMembersCount": "0"},
            ]

            self.sync_service._get_all_lists.return_value = [
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="ignore2", addresses=[]),
            ]

            self.sync_service._get_list_names_to_archive.return_value = ["archive_me", "already_archived"]

            self.sync_service._get_list_names_to_delete.return_value = ["delete_me", "already_deleted"]

            self.directory_api.groups().list().execute.side_effect = [
                {"groups": existing_groups[:1], "nextPageToken": "some_token"},
                {"groups": existing_groups[1:]},
            ]

            self.sync_service.sync_mailing_lists()

            self.sync_service.create_group.assert_called_with(
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"])
            )

            self.sync_service.update_group.assert_called_with(
                "already_synced", GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
            )

            self.sync_service.delete_group.assert_called_with("delete_me")

        self.sync_service.create_group.reset_mock()
        self.sync_service.update_group.reset_mock()
        self.sync_service.delete_group.reset_mock()
        self.sync_service._get_all_lists.reset_mock()

        with self.subTest("Successful defaults with task"):
            self.sync_service.task = self.task = Task.objects.create(
                total=0, completed=0, redirect_url=reverse("admin:mailing_lists_mailinglist_changelist")
            )

            existing_groups = [
                {"name": "delete_me", "directMembersCount": "3"},
                {"name": "archive_me", "directMembersCount": "3"},
                {"name": "already_synced", "directMembersCount": "2"},
                {"name": "already_archived", "directMembersCount": "0"},
            ]

            self.sync_service._get_all_lists.return_value = [
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="ignore2", addresses=[]),
            ]

            self.sync_service._get_list_names_to_archive.return_value = ["archive_me", "already_archived"]

            self.sync_service._get_list_names_to_delete.return_value = ["delete_me", "already_deleted"]

            self.directory_api.groups().list().execute.side_effect = [
                {"groups": existing_groups[:1], "nextPageToken": "some_token"},
                {"groups": existing_groups[1:]},
            ]

            self.sync_service.sync_mailing_lists()

            self.sync_service.create_group.assert_called_with(
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"])
            )

            self.sync_service.update_group.assert_called_with(
                "already_synced", GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
            )

            self.sync_service.archive_group.assert_called_once_with("archive_me")

            self.sync_service.delete_group.assert_called_once_with("delete_me")

        self.sync_service.create_group.reset_mock()
        self.sync_service.update_group.reset_mock()
        self.sync_service.archive_group.reset_mock()
        self.sync_service.delete_group.reset_mock()
        self.sync_service._get_all_lists.reset_mock()

        with self.subTest("Successful partial"):
            self.sync_service.task = None

            existing_groups = [
                {"name": "delete_me", "directMembersCount": "3"},
                {"name": "already_synced", "directMembersCount": "2"},
                {"name": "ignore", "directMembersCount": "0"},
            ]

            self.sync_service._get_list_names_to_archive.return_value = ["archive_me", "already_archived"]

            self.sync_service._get_list_names_to_delete.return_value = ["delete_me", "already_deleted"]

            self.directory_api.groups().list().execute.side_effect = [
                {"groups": existing_groups[:1], "nextPageToken": "some_token"},
                {"groups": existing_groups[1:]},
            ]

            self.sync_service.sync_mailing_lists(
                [
                    GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"]),
                    GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
                    GSuiteSyncService.GroupData(name="ignore2", addresses=[]),
                ]
            )

            self.sync_service.create_group.assert_called_with(
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"])
            )

            self.sync_service.update_group.assert_called_with(
                "already_synced", GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
            )

            self.sync_service.archive_group.assert_not_called()
            self.sync_service.delete_group.assert_not_called()

        self.sync_service.create_group.reset_mock()
        self.sync_service.update_group.reset_mock()
        self.sync_service.archive_group.reset_mock()
        self.sync_service.delete_group.reset_mock()
        self.sync_service._get_all_lists.reset_mock()

        with self.subTest("Non-success archiving and deleting"):
            self.sync_service.task = self.task = Task.objects.create(
                total=0, completed=0, redirect_url=reverse("admin:mailing_lists_mailinglist_changelist")
            )

            existing_groups = [
                {"name": "delete_me", "directMembersCount": "3"},
                {"name": "archive_me", "directMembersCount": "3"},
                {"name": "already_synced", "directMembersCount": "2"},
                {"name": "already_archived", "directMembersCount": "0"},
            ]

            self.sync_service._get_all_lists.return_value = [
                GSuiteSyncService.GroupData(name="sync_me", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="already_synced", addresses=["someone"]),
                GSuiteSyncService.GroupData(name="ignore2", addresses=[]),
            ]

            self.sync_service._get_list_names_to_archive.return_value = ["archive_me", "already_archived"]

            self.sync_service._get_list_names_to_delete.return_value = ["delete_me", "already_deleted"]

            self.directory_api.groups().list().execute.side_effect = [
                {"groups": existing_groups[:1], "nextPageToken": "some_token"},
                {"groups": existing_groups[1:]},
            ]

            self.sync_service.archive_group.return_value = False
            self.sync_service.delete_group.return_value = False

            self.sync_service.sync_mailing_lists()

            self.sync_service.archive_group.assert_called_once_with("archive_me")

            self.sync_service.delete_group.assert_called_once_with("delete_me")
            # TODO: Add actual checks for this test case
            self.settings_api.reset_mock()
            self.directory_api.reset_mock()

        self.sync_service.create_group = original_create
        self.sync_service.update_group = original_update
        self.sync_service.archive_group = original_archive
        self.sync_service.delete_group = original_delete
        self.sync_service._get_all_lists = original_get_all_lists

    def test_sync_mailing_lists_as_task(self):
        original_sync_mailing_lists = self.sync_service.sync_mailing_lists
        self.sync_service.sync_mailing_lists = MagicMock()
        task_id = self.sync_service.sync_mailing_lists_as_task(lists=["test"])
        self.assertTrue(Task.objects.filter(id=task_id).exists())
        self.sync_service.sync_mailing_lists.assert_called_with(["test"])
        self.sync_service.sync_mailing_lists = original_sync_mailing_lists
