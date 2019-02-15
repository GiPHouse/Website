from django.contrib import admin

from .models import *

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question','question_type')
    list_filter = ('question','question_type')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'participant','peer')
    list_filter = ('question', 'answer', 'participant','peer')

# Register your models here.
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)

