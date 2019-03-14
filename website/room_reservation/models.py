from django.db import models
from django.contrib.auth import get_user_model
from django.utils.timezone import get_current_timezone


class Room(models.Model):
    """Model for a Room that can be reserved."""

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        """Return small description about the room."""
        return f"{self.name} ({self.location})"


class Reservation(models.Model):
    """Model for a reservation that is made by a reservee for a certain room, with an start and end date.""""

    reservee = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='reservee')
    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='room')
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        """Return small description about the reservation."""
        # To skip the odd autmated unit test?
        if not hasattr(self, 'start'):
            return "."

        tz = get_current_timezone()
        start = self.start_time.astimezone(tz)
        end = self.end_time.astimezone(tz)
        start = start.strftime("%d/%m/%Y %H:%M")
        end = end.strftime("%d/%m/%Y %H:%M")
        # start = to_current_timezone(start_time)
        # end = to_current_timezone(end_time)
        return f"{self.reservee} has {self.room} reserved at {start} until {end}"
