"""Module containing the model definition for the member model."""

from typing import TYPE_CHECKING, Optional

from django.db import models
from django.db.models import OneToOneField, QuerySet
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from .address import Address
from .choices import Genders
from .user import User

if TYPE_CHECKING:
    from .membership import Membership
    from .study_registration import StudyRegistration


class MemberDetails(TimeStampedModel):
    """Model that defines the properties for a member of Loefbijter.

    This model contains the required details for a person to be a member of Loefbijter.
    Thus, it will only exist on a `Person` object when the person is a member.

    Attributes
    ----------
    user : ~loefsys.users.models.user.User
        The user that the membership details are for.
    gender : ~loefsys.contacts.models.choices.Genders
        The gender of the person.
    birthday : ~datetime.date
        The birthday of the member.
    show_birthday : bool
        Flag to determine the person's preference to publicly show their birthday.

        If set to `True`, other people will be able to see this person's birthday in
        loefsys.
    address : ~loefsys.users.models.address.Address or None
        The address of the member.
    study_registration: ~loefsys.users.models.study_registration.StudyRegistration \
        or None
        The study registration for this member.

        If this value is `None`, then this member does not study.
    membership_set : ~django.db.models.query.QuerySet of \
        ~loefsys.users.models.membership.Membership
    """

    user = models.OneToOneField(
        to=User, on_delete=models.CASCADE, related_name="member", primary_key=True
    )

    gender = models.PositiveSmallIntegerField(choices=Genders, verbose_name=_("Gender"))
    birthday = models.DateField(verbose_name=_("Birthday"))
    show_birthday = models.BooleanField(verbose_name=_("Display birthday"))

    address = OneToOneField(to=Address, on_delete=models.SET_NULL, null=True)
    study_registration: Optional["StudyRegistration"]
    membership_set: QuerySet["Membership"]
