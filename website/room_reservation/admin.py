from django.contrib import admin

from room_reservation.models import Reservation, Room


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin class for Reservation."""

    list_display = ('reservee', 'room', 'start_time', 'end_time')
    list_filter = ('room', 'start_time', 'end_time')

    def has_add_permission(self, request):
        """Reservation should only be added through the frontend."""
        return False

    def has_change_permission(self, request, obj=None):
        """Reservation should only be changed through the frontend."""
        return False


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    """Admin class for Room."""

    list_display = ('name', 'location')
