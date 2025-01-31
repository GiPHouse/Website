"""Module containing the definition for the group membership model."""

import datetime

from django.contrib.auth import get_user_model
from django.db import models
from django.db.models import QuerySet
from django.db.models.functions import Now
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from .group import LoefbijterGroup


class GroupMembershipManager(models.Manager["GroupMembership"]):
    """Manager for the :class:`~loefsys.groups.models.group.LoefbijterGroup` model.

    TODO add tests for `active` method.
    """

    def active(self) -> QuerySet["GroupMembership"]:
        """Filter and return only active group memberships.

        Returns
        -------
        ~django.db.models.query.QuerySet of \
            ~loefsys.groups.models.membership.GroupMembership
            A query of filtered memberships that are active.
        """
        return self.filter(member_until__lte=Now())


class GroupMembership(TimeStampedModel):
    """Describes a group membership.

    It is the link between the many-to-many relationship of
    :class:`~loefsys.groups.models.group.LoefbijterGroup` and
    :class:`~loefsys.contacts.models.contact.Contact`.

    TODO currently this is not used. @Jort Find a way to integrate this effectively.

    Attributes
    ----------
    created : ~datetime.datetime
        The date and time that this model was created.
    modified : ~datetime.datetime
        The date and time that this model was last modified.
    group : ~loefsys.groups.models.group.LoefbijterGroup
        The group that the membership applies to.
    contact : ~loefsys.contacts.models.Contact or None
        The person that the membership applies to. It is set to ``None`` when the user
        is removed for privacy.
    chair : bool
        Defines whether this member has admin privileges for this group.
    role : str
        The role of the member, if applicable.
    member_since : ~datetime.date
        The date that the person became member of the group.
    member_until : ~datetime.date
        The date that the member left/leaves the group.
    note : str
        A potential note on this membership.
        TODO is this needed?
    """

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, verbose_name=_("user")
    )
    group = models.ForeignKey(
        LoefbijterGroup, on_delete=models.CASCADE, verbose_name=_("group")
    )

    chair = models.BooleanField(verbose_name=_("chair"), default=False)
    role = models.CharField(
        _("role"), help_text=_("The role of this member"), max_length=255, blank=True
    )
    member_since = models.DateField(
        verbose_name=_("member since"),
        help_text=_("The date this member joined in this role"),
        default=datetime.date.today,
    )
    member_until = models.DateField(
        verbose_name=_("member until"),
        help_text=_("A member until this time."),
        blank=True,
        null=True,
    )

    note = models.CharField(max_length=256, blank=True)

    def __str__(self):
        return f"Membership of {self.contact} for {self.group}"
