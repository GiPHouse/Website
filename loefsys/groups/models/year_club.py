"""Module containing the model definition for a year club."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .group import LoefbijterGroup


class YearClub(LoefbijterGroup):
    """A year club consists of a group people belonging to the same year.

    TODO @Mark expand on this

    Attributes
    ----------
    year : int
        The year of the year club.
    """

    year = models.PositiveIntegerField(verbose_name=_("Year"))
