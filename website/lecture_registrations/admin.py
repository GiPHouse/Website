from django.contrib import admin

from lecture_registrations.models import LectureRegistration


@admin.register(LectureRegistration)
class LectureRegistrationAdmin(admin.ModelAdmin):
    """Admin class for LectureRegistrations."""

    list_display = (
        "lecture",
        "employee",
    )
    list_filter = (
        "lecture__course",
        "lecture__semester",
    )
