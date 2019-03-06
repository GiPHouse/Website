from django.contrib import admin

from .models import Reservation, Room


@admin.register(Reservation)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('reservee', 'room', 'start_time', 'end_time')
    list_filter = ('reservee', 'room', 'start_time', 'end_time')


@admin.register(Room)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('name', 'location')
    list_filter = ('name', 'location')
