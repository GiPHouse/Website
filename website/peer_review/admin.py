from django.contrib import admin

from peer_review.models import Question, Questionnaire, QuestionnaireSubmission


class QuestionInline(admin.TabularInline):
    """Inline form element for Questionnaire."""

    model = Question


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """Add Questionnaire editing in the admin."""

    inlines = (QuestionInline,)


admin.site.register(QuestionnaireSubmission)
