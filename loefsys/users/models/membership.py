"""Module defining the Loefbijter membership model."""

from collections.abc import Iterable
from datetime import MAXYEAR, date

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from .choices import MembershipTypes
from .member import MemberDetails


class Membership(models.Model):
    """Model defining a person's membership of Loefbijter.

    Over the course of a member's presence at Loefbijter, their membership status may
    change. For example, an active member may become a passive member, or an
    exceptional member becomes alumnus. This model exists to keep a record of those
    statuses and status changes.

    This also means that a person's membership period with one status may not overlap
    with a period of another membership status. When a person's membership status
    changes, the record of that status ends on day X and the record of the next status
    starts on the next day, day X+1. Validation logic is in place to ensure this
    integrity.

    Attributes
    ----------
    member : ~loefsys.contacts.models.member.LoefbijterMember
        The person that this membership belongs to.
    membership_type : ~loefsys.contacts.models.choices.MembershipTypes
        The type of membership.
    start : ~datetime.date
        The start date of the person's membership.
    end : ~datetime.date or None
        The end date of the person's membership, if it exists.
    """

    member = models.ForeignKey(
        to=MemberDetails, on_delete=models.CASCADE, verbose_name=_("Member")
    )
    membership_type = models.PositiveSmallIntegerField(
        choices=MembershipTypes.choices,
        default=MembershipTypes.ACTIVE,
        verbose_name=_("Membership type"),
    )
    start = models.DateField(
        verbose_name=_("Membership start"),
        help_text=_("The date the member's membership started"),
        default=date.today,
    )
    end = models.DateField(
        verbose_name=_("Membership end"),
        help_text=_("The date the member's membership ends/ended."),
        default=None,
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"Membership ${self.membership_type} for {self.member.user.display_name}"

    def clean(self):
        """Run validation on the model."""
        super().clean()

        if self.end and self.end < self.start:
            raise ValidationError({"end": _("End date can't be before start date.")})

        memberships = self.member.membership_set.all()
        if validate_has_overlap(self, memberships):
            raise ValidationError(
                {
                    "start": _("The membership overlaps with existing memberships."),
                    "end": _("The membership overlaps with existing memberships."),
                }
            )


# Eventually move to a utils module as reservations and events may need this logic too.
def validate_has_overlap(
    to_check: Membership, memberships: Iterable[Membership]
) -> bool:
    """Ensure non-overlapping memberships.

    It checks the date range of the updated membership and compares it to existing
    memberships for the given user. Overlap exists when the end date of one membership
    is equal to or later than the start date of another.

    Parameters
    ----------
    to_check : Membership
        The updated membership.
    memberships : Iterable of Membership
        The set of memberships belonging to the user.

    Returns
    -------
    bool
        `True` if overlap exists and `False` if no overlap exists.
    """
    max_date = date(MAXYEAR, 12, 31)
    for other in memberships:
        if to_check.pk == other.pk:
            continue

        last_start = max(to_check.start, other.start)
        first_end = min(to_check.end or max_date, other.end or max_date)
        if last_start <= first_end:
            return True
    return False
