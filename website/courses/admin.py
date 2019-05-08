from django.contrib import admin

from courses.forms import AdminSemesterForm
from courses.models import Course, Lecture, Semester


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    """Admin for the Lecture objects with filters enabled."""

    list_filter = ('course', 'semester__season', 'semester__year', 'teacher')


@admin.register(Semester)
class AdminSemester(admin.ModelAdmin):
    """Admin for the Semester Object using a custom form."""

    form = AdminSemesterForm


admin.site.register(Course)
