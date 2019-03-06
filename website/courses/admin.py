from django.contrib import admin

from courses.models import Semester, Lecture


@admin.register(Lecture)
class LectureAdmin(admin.ModelAdmin):
    """Admin for the Lecture objects with filters enabled."""

    list_filter = ('course', 'semester__season', 'semester__year', 'teacher')


admin.site.register(Semester)
