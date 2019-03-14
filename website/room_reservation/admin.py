from django.contrib import admin

from .models import Reservation, Room


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin class for Reservation."""

    list_display = ('reservee', 'room', 'start_time', 'end_time')
    list_filter = ('reservee', 'room', 'start_time', 'end_time')


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin class for Room."""

    list_display = ('name', 'location')
    list_filter = ('name', 'location')
