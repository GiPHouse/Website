from enum import Enum

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils import timezone


def current_year():
    """Wrap a call to timezone returning the current year."""
    return timezone.now().year


def max_value_current_year(value):
    """Validate value, limit modelinput to current_year, call current_year to keep validator from changing per year."""
    return MaxValueValidator(current_year()+1)(value)


class SeasonChoice(Enum):
    """Enum object for the possible seasons."""

    spring = "Spring"
    fall = "Fall"

    def __str__(self):
        """Return value of SeasonChoice object."""
        return self.value


class Course(models.Model):
    """Model to represent course."""

    name = models.CharField(max_length=50)

    def __str__(self):
        """Return name of course."""
        return f'{self.name}'


class SemesterManager(models.Manager):
    """Manager for the Semester model."""

    def get_current_registration(self):
        """Return the current registration (not in the future) that is active."""
        return self.filter(registration_start__lte=timezone.now(),
                           registration_end__gte=timezone.now()).order_by('-registration_end')[:1]


class Semester(models.Model):
    """Model for a semester (a year and a season)."""

    class Meta:
        """
        The semesters are ordered chronologically in descending order.

        For example:
        - Fall 2019 comes before spring 2019.
        - Spring 2019 comes before fall 2018.
        """

        ordering = ['-year', 'season']

    year = models.IntegerField(validators=[MinValueValidator(2008), max_value_current_year])
    season = models.CharField(
        max_length=6,
        choices=[(tag.name, tag.value) for tag in SeasonChoice],
        default=SeasonChoice.spring.name
    )

    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()

    objects = SemesterManager()

    def __str__(self):
        """Return semester season and year as string."""
        return f'{self.get_season_display()} {self.year}'


def get_slides_filename(instance, filename):
    """
    Generate slides filename.

    :param instance: Lecture instance
    :param filename: name of uploaded file
    :return: Name of file to save.
    """
    return (
        f'courses/slides/'
        f'{ instance.course }-'
        f'{ instance.title }-'
        f'{ instance.date.strftime("%d-%b-%Y") }'
        f'.pdf'
    )


class Lecture(models.Model):
    """Lecture model."""

    class Meta:
        """
        Meta class for Lecture model.

        Describing that course and title should be unique together.
        """

        unique_together = (
            ('course', 'title',),
        )

    date = models.DateField()

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )

    semester = models.ForeignKey(
        Semester,
        on_delete=models.CASCADE
    )

    title = models.CharField(
        max_length=50,
    )

    description = models.TextField(
        blank=True,
        null=True,
    )

    teacher = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    location = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )

    slides = models.FileField(
        upload_to=get_slides_filename,
        validators=[FileExtensionValidator(['pdf'])],
        blank=True,
        null=True,
    )

    def __str__(self):
        """Return value of Lecture and date object."""
        return f'{ self.course } ({ self.date })'
