"""Module containing a utility mixin for handling names of persons."""

from django.db import models
from django.db.models import F, Value, When
from django.db.models.functions import Concat
from django.utils.translation import gettext_lazy as _

from loefsys.users.models.choices import DisplayNamePreferences


class NameMixin(models.Model):
    """A mixin for dealing with names.

    Attributes
    ----------
    first_name : str
        The first name of the person.
    last_name : str
        The last name of the person.
    initials : str
        The initials of the person.
    nickname : str
        The nickname of the person, or an empty string if not applicable.
    display_name_preference : ~loefsys.users.models.choices.DisplayNamePreference
        The person's preference for having their name displayed.
    display_name : str
        A generated value of the person's name according to their preference.
    """

    first_name = models.CharField(max_length=64, verbose_name=_("First name"))
    last_name = models.CharField(max_length=64, verbose_name=_("Last name"))
    initials = models.CharField(max_length=20, verbose_name=_("Initials"), blank=True)
    nickname = models.CharField(max_length=30, verbose_name=_("Nickname"), blank=True)
    display_name_preference = models.PositiveSmallIntegerField(
        choices=DisplayNamePreferences, default=DisplayNamePreferences.FULL
    )
    display_name = models.GeneratedField(
        expression=models.Case(
            models.When(
                display_name_preference=DisplayNamePreferences.FULL_WITH_NICKNAME,
                then=Concat(
                    F("first_name"),
                    Value(" '"),
                    F("nickname"),
                    Value("' "),
                    F("last_name"),
                ),
            ),
            When(
                display_name_preference=DisplayNamePreferences.NICKNAME_LASTNAME,
                then=Concat(F("nickname"), Value(" "), F("last_name")),
            ),
            When(
                display_name_preference=DisplayNamePreferences.INITIALS_LASTNAME,
                then=Concat(F("initials"), Value(" "), F("last_name")),
            ),
            When(
                display_name_preference=DisplayNamePreferences.FIRSTNAME_ONLY,
                then=F("first_name"),
            ),
            When(
                display_name_preference=DisplayNamePreferences.NICKNAME_ONLY,
                then=F("nickname"),
            ),
            default=Concat(F("first_name"), Value(" "), F("last_name")),
        ),
        output_field=models.CharField(max_length=128),
        db_persist=True,
    )

    class Meta:
        abstract = True
