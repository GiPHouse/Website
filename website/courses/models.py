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

        Given that there is no deterministic way to determine the start of the semesters,
        we start the semesters at reasonable dates that are close to the actual start dates.

        The spring semester starts on the 10 days before the monday in the last week of january.
        The fall semester starts on september 1st.

        August is considered spring semester for simplicity.
        """
        jan31 = timezone.now().replace(
            year=timezone.now().year, month=1, day=31, hour=0, minute=0, second=0, microsecond=0
        )

        spring_semester_start = jan31 - timezone.timedelta(days=jan31.weekday()) - timezone.timedelta(days=10)

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

        unique_together = (("course", "title", "semester"),)

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

    capacity = models.PositiveSmallIntegerField(null=True, blank=True)

    register_until = models.DateTimeField(null=True, blank=True)

    @property
    def can_register(self):
        """Return True if users should be able to (un)register for this lecture at this point in time."""
        return not (self.registration_required and self.register_until and timezone.now() > self.register_until)

    @property
    def registration_required(self):
        """Is registration for this lecture enabled."""
        return self.register_until is not None

    @property
    def capacity_reached(self):
        """Is the registration capacity for this lecture reached."""
        return self.capacity is not None and self.lectureregistration_set.count() >= self.capacity

    @property
    def registered_users(self):
        """Return a list of employees that are registered for this lecture."""
        return self.lectureregistration_set.values_list("employee", flat=True)

    def __str__(self):
        """Return value of Lecture and date object."""
        return f"{ self.course } ({ self.date })"
