"""
GSuite syncing helpers defined by the mailing lists package.

This code is based on concrexit by the technicie of svthalia.
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
import logging
import threading
from random import random
from time import sleep

from django.conf import settings
from django.urls import reverse
from django.utils.datastructures import ImmutableList

from google.oauth2 import service_account

from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from googleapiclient.errors import HttpError

from mailing_lists.models import MailingList, MailingListToBeDeleted

from tasks.models import Task

logger = logging.getLogger("gsuitesync")


class MemoryCache(Cache):
    """Cache http requests in memory."""

    _CACHE = {}

    def get(self, url):
        """Get the cached result for a url."""
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        """Set the cached result for a url."""
        MemoryCache._CACHE[url] = content


memory_cache = MemoryCache()


class GSuiteSyncService:
    """Services for syncing groups and settings for groups."""

    class GroupData:
        """Store data for GSuite groups to sync them."""

        def __init__(
            self,
            name,
            description="",
            aliases=ImmutableList([]),
            addresses=ImmutableList([]),
            gsuite_group_name=None,
        ):
            """
            Create group data to sync with Gsuite.

            :param name: Name of group
            :param description: Description of group
            :param aliases: Aliases of group
            :param addresses: Addresses in group
            :param gsuite_group_name: The name of the group stored in GSuite
            """
            super().__init__()
            self.name = name
            self.gsuite_group_name = gsuite_group_name
            self.description = description
            self.aliases = aliases
            self.addresses = sorted(set(addresses))

        def __eq__(self, other):
            """
            Compare group data by comparing properties.

            :param other: Group to compare with
            :return: True if groups are equal, otherwise False.
            """
            if isinstance(other, self.__class__):
                return self.__dict__ == other.__dict__
            return False

    def __init__(self, groups_settings_api=None, directory_api=None):
        """
        Create GSuite Sync Service with the possibility to create your own group settings and directory api.

        :param groups_settings_api: Group settings api object, created if not specified
        :param directory_api: Directory api object, created if not specified
        """
        super().__init__()

        if groups_settings_api is None or directory_api is None:
            credentials = service_account.Credentials.from_service_account_info(
                settings.GSUITE_ADMIN_CREDENTIALS, scopes=settings.GSUITE_SCOPES
            ).with_subject(settings.GSUITE_ADMIN_USER)

            if groups_settings_api is None:
                groups_settings_api = build(
                    "groupssettings",
                    "v1",
                    credentials=credentials,
                    cache=memory_cache,
                )

            if directory_api is None:
                directory_api = build(
                    "admin",
                    "directory_v1",
                    credentials=credentials,
                    cache=memory_cache,
                )

        self.groups_settings_api = groups_settings_api
        self.directory_api = directory_api
        self.task = None

    @staticmethod
    def _group_settings():
        """
        Get group settings dictionary.

        :return: The group settings dictionary
        """
        return {
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
        }

    def create_group(self, group):
        """
        Create a new group based on the provided data.

        :param group: GroupData to create a group for
        """
        try:
            self.directory_api.groups().insert(
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            # Wait for mailing list creation to complete Docs say we need to
            # wait a minute.
            n = 0
            while True:
                sleep(min(2**n + random(), 64))
                try:
                    self.groups_settings_api.groups().update(
                        groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                        body=self._group_settings(),
                    ).execute()
                    break
                except HttpError as e:
                    if n > 6:
                        raise e
                    else:
                        n += 1
        except HttpError:
            logger.exception(f"Could not successfully finish creating the list {group.name}:")
            return False

        self._update_group_members(group)
        self._update_group_aliases(group)

        return True

    def update_group(self, gsuite_group_name, group):
        """
        Update a group based on the provided name and data.

        :param gsuite_group_name: old group name
        :param group: new group data
        """
        try:
            self.directory_api.groups().update(
                groupKey=f"{gsuite_group_name}@{settings.GSUITE_DOMAIN}",
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            self.groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}",
                body=self._group_settings(),
            ).execute()
            logger.info(f"List {group.name} updated")
        except HttpError:
            logger.exception(f"Could not update list {group.name}")
            return False

        self._update_group_members(group)
        self._update_group_aliases(group)

        return True

    def _update_group_aliases(self, group):
        """
        Update the aliases of a group based on existing values.

        :param group: group data
        """
        try:
            aliases_response = (
                self.directory_api.groups()
                .aliases()
                .list(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                )
                .execute()
            )
        except HttpError:
            logger.exception(f"Could not obtain existing aliases for list {group.name}:")
            return

        existing_aliases = [a["alias"] for a in aliases_response.get("aliases", [])]
        new_aliases = [f"{a}@{settings.GSUITE_DOMAIN}" for a in group.aliases]

        remove_list = [x for x in existing_aliases if x not in new_aliases]
        insert_list = [x for x in new_aliases if x not in existing_aliases]

        batch = self.directory_api.new_batch_http_request()
        for remove_alias in remove_list:
            batch.add(
                self.directory_api.groups()
                .aliases()
                .delete(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", alias=remove_alias)
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not remove an alias for list {group.name}")

        batch = self.directory_api.new_batch_http_request()
        for insert_alias in insert_list:
            batch.add(
                self.directory_api.groups()
                .aliases()
                .insert(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", body={"alias": insert_alias})
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not insert an alias for list {group.name}")

        logger.info(f"List {group.name} aliases updated")

    def archive_group(self, name):
        """
        Archive the given mailing list.

        :param name: Group name

        :return: True if the operation succeeded, False otherwise.
        """
        try:
            self.groups_settings_api.groups().patch(
                groupUniqueId=f"{name}@{settings.GSUITE_DOMAIN}",
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
            ).execute()
            self._update_group_members(GSuiteSyncService.GroupData(name, addresses=[]))
            self._update_group_aliases(GSuiteSyncService.GroupData(name, aliases=[]))
            logger.info(f"List {name} archived")
            return True
        except HttpError:
            logger.exception(f"Could not archive list {name}")
            return False

    def delete_group(self, name):
        """
        Delete the given mailing list.

        :param name: Group name

        :return: True if the operation succeeded, False otherwise.
        """
        try:
            self.directory_api.groups().delete(
                groupKey=f"{name}@{settings.GSUITE_DOMAIN}",
            ).execute()
            logger.info(f"List {name} deleted")
            return True
        except HttpError:
            logger.exception(f"Could not delete list {name}")
            return False

    def _update_group_members(self, group):
        """
        Update the group members of the specified group based on the existing members.

        :param group: group data
        """
        try:
            members_response = (
                self.directory_api.members()
                .list(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                )
                .execute()
            )
            members_list = members_response.get("members", [])
            while "nextPageToken" in members_response:
                members_response = (
                    self.directory_api.members()
                    .list(
                        groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",
                        pageToken=members_response["nextPageToken"],
                    )
                    .execute()
                )
                members_list += members_response.get("members", [])

            existing_members = [m["email"] for m in members_list if m["role"] == "MEMBER"]
            existing_managers = [m["email"] for m in members_list if m["role"] == "MANAGER"]
        except HttpError:
            logger.exception(f"Could not obtain list member data for {group.name}")
            return  # the list does not exist or something else is wrong
        new_members = group.addresses

        remove_list = [x for x in existing_members if x not in new_members]
        insert_list = [x for x in new_members if x not in existing_members and x not in existing_managers]

        batch = self.directory_api.new_batch_http_request()
        for remove_member in remove_list:
            batch.add(
                self.directory_api.members().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", memberKey=remove_member
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not remove a list member from {group.name}")

        batch = self.directory_api.new_batch_http_request()
        for insert_member in insert_list:
            batch.add(
                self.directory_api.members().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", body={"email": insert_member, "role": "MEMBER"}
                )
            )

        try:
            batch.execute()
        except HttpError:
            logger.exception(f"Could not insert a list member in {group.name}")

        logger.info(f"List {group.name} members updated")

    @staticmethod
    def mailing_list_to_group(mailing_list):
        """Convert a mailing list model to everything we need for GSuite."""
        return GSuiteSyncService.GroupData(
            name=mailing_list.address,
            gsuite_group_name=mailing_list.gsuite_group_name,
            description=mailing_list.description,
            aliases=(
                [x.address for x in mailing_list.mailinglistalias_set.all()] if mailing_list.pk is not None else []
            ),
            addresses=(list(mailing_list.all_addresses) if mailing_list.pk is not None else []),
        )

    def _get_all_lists(self):
        """
        Get all lists from the model and the automatic lists.

        :return: List of all mailing lists as GroupData
        """
        return [self.mailing_list_to_group(mailinglist) for mailinglist in MailingList.objects.all()]

    def _get_list_names_to_delete(self):
        """
        Get all lists to be deleted that were deleted in Django since the last synchronization.

        :return: List of the names of all mailing lists that should be deleted.
        """
        return [
            mailinglist.address
            for mailinglist in MailingListToBeDeleted.objects.filter(archive_instead_of_delete=False)
        ]

    def _get_list_names_to_archive(self):
        """
        Get all lists to be archived that were deleted in Django since the last synchronization.

        :return: List of the names of all mailing lists that should be archived.
        """
        return [
            mailinglist.address
            for mailinglist in MailingListToBeDeleted.objects.filter(archive_instead_of_delete=True)
        ]

    def next_task(self):
        """Increment completed counter of task if task exists."""
        if self.task:
            self.task.completed += 1
            self.task.save()

    def task_failed(self, e):
        """Log exception and set task status to fail if task exists."""
        logger.exception(e)
        if self.task:
            self.task.fail = True
            self.task.save()

    def sync_mailing_lists(self, lists=None):
        """
        Sync mailing lists with GSuite.

        Lists are only deleted if all lists are synced and thus no lists are passed to this function.

        :param lists: optional parameter to determine which lists to sync
        """
        logger.info("Starting synchronization with Gsuite.")
        remove_lists = lists is None
        if lists is None:
            lists = self._get_all_lists()

        try:
            groups_response = self.directory_api.groups().list(domain=settings.GSUITE_DOMAIN).execute()
            groups_list = groups_response.get("groups", [])
            while "nextPageToken" in groups_response:
                groups_response = (
                    self.directory_api.groups()
                    .list(
                        domain=settings.GSUITE_DOMAIN,
                        pageToken=groups_response["nextPageToken"],
                    )
                    .execute()
                )
                groups_list += groups_response.get("groups", [])
            existing_groups = [g["name"] for g in groups_list if int(g["directMembersCount"]) > 0]
            archived_groups = [g["name"] for g in groups_list if g["directMembersCount"] == "0"]
        except HttpError:
            logger.exception("Could not get the existing groups")
            return  # there are no groups or something went wrong

        new_groups = [g.gsuite_group_name if g.gsuite_group_name else g.name for g in lists if len(g.addresses) > 0]

        list_names_to_remove = self._get_list_names_to_delete()
        list_names_to_archive = self._get_list_names_to_archive()
        insert_list = [x for x in new_groups if x not in existing_groups]

        if self.task:
            self.task.total = (
                len(list_names_to_archive)
                + len(list_names_to_remove)
                + len(
                    [
                        mailinglist.name in insert_list
                        and mailinglist.name not in archived_groups
                        or len(mailinglist.addresses) > 0
                        for mailinglist in lists
                    ]
                )
            )
            self.task.completed = 0
            self.task.save()

        for mailinglist in lists:
            try:
                if mailinglist.name in insert_list and mailinglist.name not in archived_groups:
                    logger.debug(f"Starting create group of {mailinglist.name}")
                    if self.create_group(mailinglist):
                        MailingList.objects.filter(address=mailinglist.name).update(gsuite_group_name=mailinglist.name)
                elif len(mailinglist.addresses) > 0:
                    logger.debug(f"Starting update group of {mailinglist.name}")
                    if self.update_group(
                        mailinglist.gsuite_group_name if mailinglist.gsuite_group_name else mailinglist.name,
                        mailinglist,
                    ):
                        MailingList.objects.filter(address=mailinglist.name).update(gsuite_group_name=mailinglist.name)
            except Exception as e:
                self.task_failed(e)
            self.next_task()

        if remove_lists:
            for list_name in list_names_to_remove:
                success = True
                try:
                    if list_name in existing_groups or list_name in archived_groups:
                        logger.debug(f"Starting delete group of {list_name}")
                        success = self.delete_group(list_name)
                    if success:
                        MailingListToBeDeleted.objects.filter(address=list_name).delete()
                    else:
                        self.task.fail = True
                except Exception as e:
                    self.task_failed(e)
                self.next_task()

            for list_name in list_names_to_archive:
                success = True
                try:
                    if list_name in existing_groups:
                        logger.debug(f"Starting archive group of {list_name}")
                        success = self.archive_group(list_name)
                    if success:
                        MailingListToBeDeleted.objects.filter(address=list_name).delete()
                    else:
                        self.task.fail = True
                except Exception as e:
                    self.task_failed(e)
                self.next_task()

        logger.info("Synchronization ended.")

    def sync_mailing_lists_as_task(self, lists=None):
        """Sync all selected mailing lists to GSuite as a Task."""
        self.task = Task.objects.create(redirect_url=reverse("admin:mailing_lists_mailinglist_changelist"))
        thread = threading.Thread(target=self.sync_mailing_lists, args=(lists,))
        thread.start()
        return self.task.id
