from django.apps import AppConfig


class LectureRegistrationsConfig(AppConfig):
    """Appconfig for lecture registrations."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "lecture_registrations"
    verbose_name = "Lecture registrations"
