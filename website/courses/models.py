from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def current_year():
    """Wrap a call to timezone returning the current year."""
    return timezone.now().year


def max_value_current_year(value):
    """Validate value, limit modelinput to current_year, call current_year to keep validator from changing per year."""
    return MaxValueValidator(current_year() + 1)(value)


def current_season():
    """Return the current season based on the current time."""
    if timezone.now() < timezone.now().replace(month=8, day=1):
        return Semester.SPRING
    return Semester.FALL


class CourseManager(models.Manager):
    """Manager for the Course model."""

    def se(self):
        """Create Software Engineering course."""
        return self.get(name="Software Engineering")

    def sde(self):
        """Create System Development Management course."""
        return self.get(name="System Development Management")

    def sdm(self):
        """Create Software Development Entrepreneurship course."""
        return self.get(name="Software Development Entrepreneurship")


class Course(models.Model):
    """Model to represent course."""

    name = models.CharField(max_length=50)

    objects = CourseManager()

    def __str__(self):
        """Return name of course."""
        return f"{self.name}"


class SemesterManager(models.Manager):
    """Manager for the Semester model."""

    def get_current_semester(self):
        """Return the current semester based on the current time."""
        try:
            return self.get(year=current_year(), season=current_season())
        except Semester.DoesNotExist:
            self.none()


class Semester(models.Model):
    """Model for a semester (a year and a season)."""

    class Meta:
        """
        The semesters are ordered chronologically in descending order.

        For example:
        - Fall 2019 comes before spring 2019.
        - Spring 2019 comes before fall 2018.
        """

        ordering = ["-year", "-season"]
        unique_together = [["year", "season"]]

    SPRING = 0
    FALL = 1
    CHOICES = ((SPRING, "Spring"), (FALL, "Fall"))

    year = models.IntegerField(validators=[MinValueValidator(2008), max_value_current_year])
    season = models.PositiveSmallIntegerField(choices=CHOICES, default=SPRING)

    registration_start = models.DateTimeField(
        blank=True, null=True, help_text="This must be filled in to open the registration."
    )
    registration_end = models.DateTimeField(
        blank=True, null=True, help_text="This must be filled in to open the registration."
    )

    objects = SemesterManager()

    def registration_open(self):
        """Return if registration is open."""
        if self.registration_start is None or self.registration_end is None:
            return False
        return self.registration_start <= timezone.now() <= self.registration_end

    def __str__(self):
        """Return semester season and year as string."""
        return f"{self.get_season_display()} {self.year}"


def get_slides_filename(instance, filename):
    """
    Generate slides filename.

    :param instance: Lecture instance
    :param filename: name of uploaded file
    :return: Name of file to save.
    """
    return (
        f"courses/slides/"
        f"{ instance.course }-"
        f"{ instance.title }-"
        f'{ instance.date.strftime("%d-%b-%Y") }'
        f".pdf"
    )


class Lecture(models.Model):
    """Lecture model."""

    class Meta:
        """
        Meta class for Lecture model.

        Describing that course and title should be unique together.
        """

        unique_together = (("course", "title"),)

    date = models.DateField()

    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)

    title = models.CharField(max_length=50)

    description = models.TextField(blank=True, null=True)

    teacher = models.CharField(max_length=50, blank=True, null=True)

    location = models.CharField(max_length=50, blank=True, null=True)

    slides = models.FileField(
        upload_to=get_slides_filename, validators=[FileExtensionValidator(["pdf"])], blank=True, null=True
    )

    def __str__(self):
        """Return value of Lecture and date object."""
        return f"{ self.course } ({ self.date })"
