"""Module containing the model definitions for a board."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .group import LoefbijterGroup


class Board(LoefbijterGroup):
    """A group model for the board of Loefbijter.

    TODO @Mark expand on this.

    Attributes
    ----------
    year : int
        The year of the board, starting in the founding year.
    """

    year = models.PositiveIntegerField(verbose_name=_("Year"))
