from django import forms
from django.utils import timezone

from courses.models import Semester


def year_choices():
    """Return years from 2008 to next year."""
    return [(r, r) for r in range(2008, timezone.now().year + 2)]


class AdminSemesterForm(forms.ModelForm):
    """Semester Object form with typed choices for the year."""

    year = forms.TypedChoiceField(coerce=int, choices=year_choices, initial=timezone.now().year)

    class Meta:
        """Link SemesterForm to Semester model."""

        model = Semester
        exclude = []
