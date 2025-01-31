"""Module containing the model definitions for a committee."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from .group import LoefbijterGroup


class Committee(LoefbijterGroup):
    """Model representing a committee.

    TODO @Mark expand on this

    Attributes
    ----------
    mandatory : bool
        A flag that shows whether the committee is a mandatory committee. If a committee
        is one of the mandatory committees, new members can be assigned to this
        committee to satisfy their committee duty.
    """

    mandatory = models.BooleanField(
        default=False,
        help_text=_(
            "If this is checked new members should be assigned to this committee, any "
            "members that are part of this committee satisfy their committee_duty."
        ),
    )
