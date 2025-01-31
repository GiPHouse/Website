from django.test import TestCase
from django_dynamic_fixture import G

from loefsys.groups.models import (
    Board,
    Committee,
    Fraternity,
    LoefbijterGroup,
    YearClub,
)


class GroupTestCase(TestCase):
    def test_create(self):
        generic_group = G(LoefbijterGroup)
        self.assertIsNotNone(generic_group)
        self.assertIsNotNone(generic_group.pk)


class BoardTestCase(TestCase):
    def test_create(self):
        board = G(Board)
        self.assertIsNotNone(board)
        self.assertIsNotNone(board.pk)


class CommitteeTestCase(TestCase):
    def test_create(self):
        committee = G(Committee)
        self.assertIsNotNone(committee)
        self.assertIsNotNone(committee.pk)


class FraternityTestCase(TestCase):
    def test_create(self):
        fraternity = G(Fraternity)
        self.assertIsNotNone(fraternity)
        self.assertIsNotNone(fraternity.pk)


class YearClubTestCase(TestCase):
    def test_create(self):
        year_club = G(YearClub)
        self.assertIsNotNone(year_club)
        self.assertIsNotNone(year_club.pk)
