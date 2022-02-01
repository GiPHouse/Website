from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from registrations.models import Employee

User: Employee = get_user_model()


def in_special_availability(available_timeslots: [], start_time, end_time):
    """Checks whether a certain time slot is in a list of available timeslots."""
    for timeslot in available_timeslots:
        start = timezone.datetime.fromisoformat(timeslot["from"]).astimezone(timezone.get_current_timezone())
        end = timezone.datetime.fromisoformat(timeslot["until"]).astimezone(timezone.get_current_timezone())
        if start_time >= start and end_time <= end:
            return True
    return False


class Room(models.Model):
    """Model for a Room that can be reserved."""

    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    special_availability = models.JSONField(
        null=True,
        blank=True,
        help_text="If filled in, the room will only accept reservations during the specified timeslots. "
        "Enter valid JSON in the following format: "
        '[{"from":"2022-01-31|08:00","until":"2022-02-01|18:00"},'
        '{"from":"2022-02-02|15:30","until":"2022-02-02|18:00"}].',
    )

    def __str__(self):
        """Return small description about the room."""
        return f"{self.name} ({self.location})"


class Reservation(models.Model):
    """Model for a reservation that is made by a reservee for a certain room, with an start and end date."""

    reservee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    def __str__(self):
        """Return small description about the reservation."""
        return f"{self.reservee} has {self.room} reserved at {self.start_time} until {self.end_time}"
