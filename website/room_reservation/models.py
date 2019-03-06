from django.db import models
from django.contrib.auth import get_user_model


class Room(models.Model):
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.name} ({self.location})"


class Reservation(models.Model):
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
        return f"{self.reservee} has {self.room} reserved at {self.start_time} until {self.end_time}"
