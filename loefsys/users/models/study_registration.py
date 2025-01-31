"""Module containing the definition for a study registration."""

from django.core import validators
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.models import TimeStampedModel

from .member import MemberDetails


class StudyRegistration(TimeStampedModel):
    """Model for members who are registered for a study.

    Attributes
    ----------
    created : ~datetime.datetime
        The timestamp of creation of this model.
    modified : ~datetime.datetime
        The timestamp of last modification of this model.
    member : ~loefsys.contacts.models.member.LoefbijterMember
        The member whom the study details belong to.
    institution : str
        The name of the institution where the person is registered.
    programme : str
        The programme that the person follows at the institution.
    student_number : str
        The student number of the person.
    rsc_number : str
        The RSC number of the person or empty if they don't have one.
    """

    member = models.OneToOneField(
        MemberDetails, on_delete=models.CASCADE, related_name="study_registration"
    )

    institution = models.CharField(
        max_length=32, verbose_name=_("Educational institution")
    )
    programme = models.CharField(max_length=32, verbose_name=_("Study programme"))
    student_number = models.CharField(
        max_length=10,
        verbose_name=_("Student number"),
        validators=[
            validators.RegexValidator(
                regex=r"(s\d{7}|[ezu]\d{6,7})",  # TODO: allow for HAN, maybe others
                message=_("Enter a valid student- or e/z/u-number."),  # or no check
            )
        ],
    )
    rsc_number = models.CharField(
        max_length=10, verbose_name=_("RSC card number"), blank=True
    )
