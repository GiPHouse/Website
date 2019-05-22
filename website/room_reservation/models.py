from django.contrib.auth import get_user_model
from django.db import models

from registrations.models import Student

User = get_user_model()


class Room(models.Model):
    """Model for a Room that can be reserved."""

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        """Return small description about the room."""
        return f"{self.name} ({self.location})"


class Reservation(models.Model):
    """Model for a reservation that is made by a reservee for a certain room, with an start and end date."""

    reservee = models.ForeignKey(
        Student,
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
        return f"{self.reservee} has {self.room} reserved at {self.start_time} until {self.end_time}"
