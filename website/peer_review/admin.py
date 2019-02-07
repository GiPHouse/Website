from django.contrib import admin

from .models import *

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question','closed_question')
    list_filter = ('question','closed_question')

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'participant','peer')
    list_filter = ('question', 'answer', 'participant','peer')

# Register your models here.
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)

