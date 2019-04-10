from django.contrib import admin
from django import forms
from django.utils import timezone


from courses.models import Semester, Lecture, Course


def year_choices():
    """Return years from 2008 to next year."""
    return [(r, r) for r in range(2008, timezone.now().year+2)]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    """Admin for the Lecture objects with filters enabled."""

    list_filter = ('course', 'semester__season', 'semester__year', 'teacher')


class AdminSemester(forms.ModelForm):
    """Semester Object form with typed choices for the year."""

    year = forms.TypedChoiceField(
        coerce=int, choices=year_choices, initial=timezone.now().year)

    class Meta:
        """Link SemesterForm to Semester model."""

        model = Semester
        exclude = []


@admin.register(Semester)
class AdminSemesterForm(admin.ModelAdmin):
    """Admin for the Semester Object using a custom form."""

    form = AdminSemester


admin.site.register(Course)
