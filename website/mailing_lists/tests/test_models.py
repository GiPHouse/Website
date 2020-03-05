from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase

from mailing_lists.models import MailingList, MailingListAlias


class ModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.existing_list_address = f"list@{settings.GSUITE_DOMAIN}"
        cls.existing_alias_address = f"alias@{settings.GSUITE_DOMAIN}"
        cls.unused_address = f"unused@{settings.GSUITE_DOMAIN}"

        cls.existing_list = MailingList.objects.create(name="ExistingList", address=cls.existing_list_address)
        cls.existing_alias = MailingListAlias.objects.create(
            address=cls.existing_alias_address, mailing_list=cls.existing_list
        )

    def test_list_validate_unique_is_valid(self):
        self.existing_list.validate_unique()

    def test_list_validate_unique_alias_exists(self):
        new_mailing_list = MailingList(name="NewList", address=self.existing_alias_address)
        with self.assertRaises(ValidationError):
            new_mailing_list.validate_unique()

    def test_alias_validate_unique_is_valid(self):
        self.existing_alias.validate_unique()

    def test_alias_validate_unique_list_exists(self):
        new_mailing_list = MailingList(name="NewList", address=self.unused_address)
        new_alias = MailingListAlias(address=self.existing_list_address, mailing_list=new_mailing_list)
        with self.assertRaises(ValidationError):
            new_alias.validate_unique()

    def test_alias_validate_unique_parent_list_has_same_email(self):
        shared_email_address = f"collision@{settings.GSUITE_DOMAIN}"
        new_mailing_list = MailingList(name="NewList", address=shared_email_address)
        new_alias = MailingListAlias(address=shared_email_address, mailing_list=new_mailing_list)
        with self.assertRaises(ValidationError):
            new_alias.validate_unique()
