from django.contrib import admin

from .models import Question, Answer


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'question_type')
    list_filter = ('question', 'question_type')


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'participant', 'peer')
    list_filter = ('question', 'answer', 'participant', 'peer')
