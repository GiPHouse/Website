from django.contrib import admin

from .models import Question, Answer, Questionnaire


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """Customize the question filters in the admin."""

    list_display = ('question', 'question_type')
    list_filter = ('question', 'question_type')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    """Customize the answer filters in the admin."""

    list_display = ('question', 'answer', 'participant', 'peer', 'on_time')
    list_filter = ('question',)

    def on_time(self, obj):
        """Wrap on_time of model, to be able to set boolean for admin checkmarks."""
        return obj.on_time

    on_time.boolean = True


class QuestionInline(admin.TabularInline):
    """Inline form element for Questionnaire."""

    model = Question


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    """Add Questionnaire editing in the admin."""

    inlines = (QuestionInline,)
