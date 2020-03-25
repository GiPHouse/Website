from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


def current_year():
    """Wrap a call to timezone returning the current year."""
    return timezone.now().year


def max_value_current_year(value):
    """Validate value, limit modelinput to current_year, call current_year to keep validator from changing per year."""
    return MaxValueValidator(current_year() + 1)(value)


class CourseManager(models.Manager):
    """Manager for the Course model."""

    def se(self):
        """Create Software Engineering course."""
        return self.get(name="Software Engineering")

    def sdm(self):
        """Create System Development Management course."""
        return self.get(name="System Development Management")

    def sde(self):
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

    def get_first_semester_with_open_registration(self):
        """Get the first semester with an open registration."""
        return self.filter(registration_start__lte=timezone.now(), registration_end__gte=timezone.now()).first()

    def get_or_create_current_semester(self):
        """
        Return the current semester based on the current time.

        Dates before the start of the spring semester are seen as the fall semester of the calendar year before.
        For example, 10 january 2020 is seen as the fall semester of 2019.

        The spring semester starts in the week that has the first week day of february.
        For example, if 2 february is a thursday, the spring semester will start on monday january 30th.
        For example, if 1 february is a saturday, the spring semester will start on monday february 3rd.

        August is considered spring semester for simplicity.
        """
        february_first = timezone.now().replace(
            year=timezone.now().year, month=2, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if february_first.weekday() < 5:
            spring_semester_start = february_first - timezone.timedelta(days=february_first.weekday())
        else:
            spring_semester_start = february_first + timezone.timedelta(days=7 - february_first.weekday())

        fall_semester_start = timezone.now().replace(
            year=timezone.now().year, month=9, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        if timezone.now() < spring_semester_start:
            return self.get_or_create(year=timezone.now().year - 1, season=Semester.FALL)[0]

        elif spring_semester_start <= timezone.now() < fall_semester_start:
            return self.get_or_create(year=timezone.now().year, season=Semester.SPRING)[0]

        # In the case fall_semester_start <= timezone.now()
        # In other words, if the start of the fall semester has passed.
        return self.get_or_create(year=current_year(), season=Semester.FALL)[0]


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

    is_archived = models.BooleanField(
        blank=False,
        null=False,
        default=False,
        help_text="Setting a semester to archived will remove all GitHub teams and archive all their repositories for "
        "this semester.",
    )

    objects = SemesterManager()

    @staticmethod
    def slug_to_season(slug_string):
        """Return season id when given a slug."""
        if slug_string.lower() == "spring":
            return Semester.SPRING

        elif slug_string.lower() == "fall":
            return Semester.FALL

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
