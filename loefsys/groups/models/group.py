"""Module defining the generic group model."""

from django.contrib.auth.models import Permission
from django.db import models
from django.db.models import Case, Q, QuerySet, When
from django.db.models.functions import Now
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel


class GroupManager[TGroup: "LoefbijterGroup"](models.Manager[TGroup]):
    """Custom manager for group models.

    The manager is used by models inheriting the
    :class:`~loefsys.groups.models.group.LoefbijterGroup` model.

    TODO add tests for `active` method.
    """

    use_in_migrations = True

    def get_by_natural_key(self, name):
        """Get an instance by its natural key."""
        return self.get(name=name)

    def active(self) -> QuerySet[TGroup]:
        """Filter and return only groups that are active.

        Returns
        -------
        ~django.db.models.query.QuerySet of ~loefsys.groups.models.group.LoefbijterGroup
            A query of filtered :class:`~loefsys.groups.models.group.LoefbijterGroup`
            implementations.
        """
        return self.filter(active=True)


class LoefbijterGroup(TimeStampedModel):
    """Describes a group of members.

    Groups are a generic way of categorizing users to apply permissions, or
    some other label, to those users. A user can belong to any number of
    groups.

    This model represents a group within Loefbijter. Subclasses exist for specific
    groups, such as boards or committees, but the generic model is also available. This
    model mirrors the behaviour of the internal Django Groups model as it provides an
    easy way of managing permissions.

    TODO add tests for active field.

    Attributes
    ----------
    name : str
        The name of the group.
    description : str
        A description of the group.
    permissions : ~django.db.models.query.QuerySet or \
        ~django.contrib.auth.models.Permission
        The permissions for this group.
    date_foundation : ~datetime.date
        The date that the group was founded on.
    date_discontinuation : ~datetime.date, None
        The date that the group ceased to exist.
    active : bool
        A flag whether the group is currently active.

        It is a property calculated by whether :attr:`.date_discontinuation` exists and
        whether the date has passed.
    display_members : bool
        A flag that determines whether the members of the group are publicly visible.
    """

    name = models.CharField(_("Name"), max_length=150, unique=True)
    description = models.TextField(verbose_name=_("Description"))
    permissions = models.ManyToManyField(
        Permission, verbose_name=_("Permissions"), blank=True
    )
    date_foundation = models.DateField(_("Date of foundation"))
    date_discontinuation = models.DateField(_("Date of discontinuation"), null=True)
    active = models.GeneratedField(  # TODO needs testing
        expression=Case(
            When(
                date_discontinuation__isnull=False,
                then=Q(date_discontinuation__gte=Now()),
            ),
            default=True,
        ),
        output_field=models.BooleanField(),
        db_persist=True,
    )
    display_members = models.BooleanField(_("Display group members"))

    objects = GroupManager()

    def __str__(self):
        return f"Group {self.name}"

    def natural_key(self):
        """Return the natural key for a group."""
        return (self.name,)
