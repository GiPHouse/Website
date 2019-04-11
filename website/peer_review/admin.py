from django.contrib import admin

from peer_review.models import Question, Answer, Questionnaire


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Customize the answer filters in the admin."""

    list_display = ('question', 'answer', 'participant', 'peer', 'on_time')
    list_filter = ('question',)
    readonly_fields = ('on_time',)


class QuestionInline(admin.TabularInline):
    """Inline form element for Questionnaire."""

    model = Question


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """Add Questionnaire editing in the admin."""

    inlines = (QuestionInline,)
