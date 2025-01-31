from datetime import date

from django.test import TestCase
from django_dynamic_fixture import G

from loefsys.users.models.address import Address
from loefsys.users.models.member import MemberDetails
from loefsys.users.models.membership import Membership, validate_has_overlap
from loefsys.users.models.study_registration import StudyRegistration


class AddressTestCase(TestCase):
    """Tests for Address model creation and validation."""

    def test_create(self):
        """Test that Address instance can be created."""
        address = G(Address)
        self.assertIsNotNone(address)
        self.assertIsNotNone(address.pk)


class MemberDetailsTestCase(TestCase):
    """Tests for Member model creation and validation."""

    def test_create(self):
        """Test that Member instance can be created."""
        member = G(MemberDetails)
        self.assertIsNotNone(member)
        self.assertIsNotNone(member.pk)


class MembershipTestCase(TestCase):
    """Tests for Membership model creation and validation."""

    def test_create(self):
        """Test that Membership instance can be created."""
        membership = G(Membership)
        self.assertIsNotNone(membership)
        self.assertIsNotNone(membership.pk)


class StudyRegistrationTestCase(TestCase):
    """Tests for StudyRegistration model creation and validation."""

    def test_create(self):
        """Test that StudyRegistration instance can be created."""
        registration = G(StudyRegistration)
        self.assertIsNotNone(registration)
        self.assertIsNotNone(registration.pk)


class MembershipOverlapTestCase(TestCase):
    """Tests for the validate_overlap function in the Membership model."""

    def setUp(self):
        self.member = G(MemberDetails)

    def test_no_overlap(self):
        """Test that there is no overlap when the membership dates don't overlap."""
        membership1 = G(
            Membership,
            member=self.member,
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertFalse(validate_has_overlap(membership1, [membership2]))

    def test_overlap(self):
        """Test that there is overlap when the membership dates overlap."""
        membership1 = G(
            Membership, member=self.member, start=date(2023, 6, 1), end=date(2024, 6, 1)
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2]))

    def test_overlap_same_start(self):
        """Test that there is overlap when the membership has the same start date."""
        membership1 = G(
            Membership, member=self.member, start=date(2023, 1, 1), end=date(2024, 6, 1)
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2]))

    def test_overlap_same_end(self):
        """Test that there is overlap when the membership has the same end date."""
        membership1 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2022, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2]))

    def test_no_overlap_null_end(self):
        """Test that there is no overlap when an ongoing membership has no end date."""
        membership1 = G(
            Membership, member=self.member, start=date(2024, 1, 1), end=None
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertFalse(validate_has_overlap(membership1, [membership2]))

    def test_overlap_null_end(self):
        """Test that there is overlap with an ongoing membership."""
        membership1 = G(
            Membership, member=self.member, start=date(2023, 6, 1), end=None
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2]))

    def test_no_overlap_multiple_memberships(self):
        """Test that no overlap occurs with non-overlapping multiple memberships."""
        membership1 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
        )
        membership3 = G(
            Membership,
            member=self.member,
            start=date(2020, 1, 1),
            end=date(2020, 12, 31),
        )
        self.assertFalse(validate_has_overlap(membership1, [membership2, membership3]))

    def test_overlap_multiple_memberships(self):
        """Test that there is overlap with multiple overlapping memberships."""
        membership1 = G(
            Membership, member=self.member, start=date(2023, 6, 1), end=date(2024, 6, 1)
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        membership3 = G(
            Membership,
            member=self.member,
            start=date(2020, 1, 1),
            end=date(2020, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2, membership3]))

    def test_overlap_same_dates(self):
        """Test that there is overlap with matching start and end dates."""
        membership1 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        membership2 = G(
            Membership,
            member=self.member,
            start=date(2023, 1, 1),
            end=date(2023, 12, 31),
        )
        self.assertTrue(validate_has_overlap(membership1, [membership2]))
