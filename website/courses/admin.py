from django.contrib import admin
from django import forms
from django.utils import timezone


from courses.models import Semester, Lecture, Course


def year_choices():
    return [(r, r) for r in range(2008, timezone.now().year+2)]


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    """Admin for the Lecture objects with filters enabled."""

    list_filter = ('course', 'semester__season', 'semester__year', 'teacher')


class SemesterForm(forms.ModelForm):
    """Semester Object form with typed choices for the year"""
    year = forms.TypedChoiceField(
        coerce=int, choices=year_choices, initial=timezone.now().year)

    class Meta:
        model = Semester
        exclude = []


class SemesterAdmin(admin.ModelAdmin):
    """Admin for the Semester Object using a custom form"""
    form = SemesterForm


admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course)
