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
import asyncio

from django.conf import settings
from django.utils.datastructures import ImmutableList

from google.oauth2 import service_account

from googleapiclient.discovery import build
from googleapiclient.discovery_cache.base import Cache
from googleapiclient.errors import HttpError

from mailing_lists.models import MailingList
from mailing_lists.services import get_automatic_lists


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
            self, name, description="", aliases=ImmutableList([]), addresses=ImmutableList([]),
        ):
            """
            Create group data to sync with Gsuite.

            :param name: Name of group
            :param description: Description of group
            :param aliases: Aliases of group
            :param addresses: Addresses in group
            """
            self.name = name
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
        if groups_settings_api is None or directory_api is None:
            credentials = service_account.Credentials.from_service_account_info(
                settings.GSUITE_ADMIN_CREDENTIALS, scopes=settings.GSUITE_SCOPES
            ).with_subject(settings.GSUITE_ADMIN_USER)

            if groups_settings_api is None:
                groups_settings_api = build("groupssettings", "v1", credentials=credentials, cache=memory_cache,)

            if directory_api is None:
                directory_api = build("admin", "directory_v1", credentials=credentials, cache=memory_cache,)

        self.groups_settings_api = groups_settings_api
        self.directory_api = directory_api

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

    async def create_group(self, group):
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
            # Wait for mailing list creation to complete. Docs say we need to
            # wait a minute.
            await asyncio.sleep(60)
            self.groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}", body=self._group_settings(),
            ).execute()
        except HttpError as e:
            print(f"Could not successfully finish creating the list {group.name}: ", e.content)
            return

        self._update_group_members(group)
        self._update_group_aliases(group)

    async def update_group(self, old_name, group):
        """
        Update a group based on the provided name and data.

        :param old_name: old group name
        :param group: new group data
        """
        try:
            self.directory_api.groups().update(
                groupKey=f"{old_name}@{settings.GSUITE_DOMAIN}",
                body={
                    "email": f"{group.name}@{settings.GSUITE_DOMAIN}",
                    "name": group.name,
                    "description": group.description,
                },
            ).execute()
            self.groups_settings_api.groups().update(
                groupUniqueId=f"{group.name}@{settings.GSUITE_DOMAIN}", body=self._group_settings(),
            ).execute()
            print(f"List {group.name} updated")
        except HttpError as e:
            print(f"Could not update list {group.name}", e.content)
            return

        self._update_group_members(group)
        self._update_group_aliases(group)

    def _update_group_aliases(self, group):
        """
        Update the aliases of a group based on existing values.

        :param group: group data
        """
        try:
            aliases_response = (
                self.directory_api.groups()
                .aliases()
                .list(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",)
                .execute()
            )
        except HttpError as e:
            print(f"Could not obtain existing aliases " f"for list {group.name}", e.content)
            return

        existing_aliases = [a["alias"] for a in aliases_response.get("aliases", [])]
        new_aliases = [f"{a}@{settings.GSUITE_DOMAIN}" for a in group.aliases]

        remove_list = [x for x in existing_aliases if x not in new_aliases]
        insert_list = [x for x in new_aliases if x not in existing_aliases]

        for remove_alias in remove_list:
            try:
                self.directory_api.groups().aliases().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", alias=remove_alias,
                ).execute()
            except HttpError as e:
                print(f"Could not remove alias " f"{remove_alias} for list {group.name}", e.content)

        for insert_alias in insert_list:
            try:
                self.directory_api.groups().aliases().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", body={"alias": insert_alias},
                ).execute()
            except HttpError as e:
                print(f"Could not insert alias " f"{insert_alias} for list {group.name}", e.content)

        print(f"List {group.name} aliases updated")

    async def delete_group(self, name):
        """
        Set the specified list to unused, this is not a real delete.

        :param name: Group name
        """
        try:
            self.groups_settings_api.groups().patch(
                groupUniqueId=f"{name}@{settings.GSUITE_DOMAIN}",
                body={"archiveOnly": "true", "whoCanPostMessage": "NONE_CAN_POST"},
            ).execute()
            self._update_group_members(GSuiteSyncService.GroupData(name, addresses=[]))
            self._update_group_aliases(GSuiteSyncService.GroupData(name, aliases=[]))
            print(f"List {name} deleted")
        except HttpError as e:
            print(f"Could not delete list {name}", e.content)

    def _update_group_members(self, group):
        """
        Update the group members of the specified group based on the existing members.

        :param group: group data
        """
        try:
            members_response = (
                self.directory_api.members().list(groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}",).execute()
            )
            members_list = members_response.get("members", [])
            while "nextPageToken" in members_response:
                members_response = (
                    self.directory_api.members()
                    .list(
                        groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", pageToken=members_response["nextPageToken"],
                    )
                    .execute()
                )
                members_list += members_response.get("members", [])

            existing_members = [m["email"] for m in members_list if m["role"] == "MEMBER"]
            existing_managers = [m["email"] for m in members_list if m["role"] == "MANAGER"]
        except HttpError as e:
            print("Could not obtain list member data", e.content)
            return  # the list does not exist or something else is wrong
        new_members = group.addresses

        remove_list = [x for x in existing_members if x not in new_members]
        insert_list = [x for x in new_members if x not in existing_members and x not in existing_managers]

        for remove_member in remove_list:
            try:
                self.directory_api.members().delete(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", memberKey=remove_member,
                ).execute()
            except HttpError as e:
                print(f"Could not remove list member " f"{remove_member} from {group.name}", e.content)

        for insert_member in insert_list:
            try:
                self.directory_api.members().insert(
                    groupKey=f"{group.name}@{settings.GSUITE_DOMAIN}", body={"email": insert_member, "role": "MEMBER"},
                ).execute()
            except HttpError as e:
                print(f"Could not insert list member " f"{insert_member} in {group.name}", e.content)

        print(f"List {group.name} members updated")

    @staticmethod
    def mailing_list_to_group(mailing_list):
        """Convert a mailing list model to everything we need for GSuite."""
        return GSuiteSyncService.GroupData(
            name=mailing_list.address,
            description=mailing_list.description,
            aliases=(
                [x.address for x in mailing_list.mailinglistalias_set.all()] if mailing_list.pk is not None else []
            ),
            addresses=(list(mailing_list.all_addresses) if mailing_list.pk is not None else []),
        )

    @staticmethod
    def _automatic_to_group(automatic_list):
        """Convert an automatic mailing list to a GSuite Group data obj."""
        return GSuiteSyncService.GroupData(
            name=automatic_list["address"],
            description=automatic_list["description"],
            aliases=automatic_list.get("aliases", []),
            addresses=automatic_list["addresses"],
        )

    def _get_all_lists(self):
        """
        Get all lists from the model and the automatic lists.

        :return: List of all mailing lists as GroupData
        """
        return [self.mailing_list_to_group(l) for l in MailingList.objects.all()] + [
            self._automatic_to_group(l) for l in get_automatic_lists()
        ]

    def sync_mailing_lists(self, lists=None):
        """
        Sync mailing lists with GSuite.

        Lists are only deleted if all lists are synced and thus no lists are passed to this function.

        :param lists: optional parameter to determine which lists to sync
        """
        remove_lists = lists is None
        if lists is None:
            lists = self._get_all_lists()

        try:
            groups_response = self.directory_api.groups().list(domain=settings.GSUITE_DOMAIN).execute()
            groups_list = groups_response.get("groups", [])
            while "nextPageToken" in groups_response:
                groups_response = (
                    self.directory_api.groups()
                    .list(domain=settings.GSUITE_DOMAIN, pageToken=groups_response["nextPageToken"],)
                    .execute()
                )
                groups_list += groups_response.get("groups", [])
            existing_groups = [g["name"] for g in groups_list if int(g["directMembersCount"]) > 0]
            archived_groups = [g["name"] for g in groups_list if g["directMembersCount"] == "0"]
        except HttpError as e:
            print("Could not get the existing groups", e.content)
            return  # there are no groups or something went wrong

        new_groups = [g.name for g in lists if len(g.addresses) > 0]

        remove_list = [x for x in existing_groups if x not in new_groups]
        insert_list = [x for x in new_groups if x not in existing_groups]

        group_tasks = []
        for l in lists:
            if l.name in insert_list and l.name not in archived_groups:
                group_tasks.append(self.create_group(l))
            elif len(l.addresses) > 0:
                group_tasks.append(self.update_group(l.name, l))

        if remove_lists:
            for l in remove_list:
                group_tasks.append(self.delete_group(l))

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(asyncio.gather(*group_tasks))
