import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import widgets

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration

student_number_regex = re.compile(r"^[sS]?(\d{7})$")
wrong_email_regex = re.compile(r"^[sS]?(\d{7})@(?:student\.)?ru\.nl$")

User: Employee = get_user_model()


class Step2Form(forms.Form):
    """Form to get user information for registration."""

    def __init__(self, *args, **kwargs):
        """Set querysets dynamically."""
        super().__init__(*args, **kwargs)

        self.fields["course"].queryset = Course.objects.all()

        self.fields["project1"].queryset = Project.objects.filter(
            semester=Semester.objects.get_first_semester_with_open_registration()
        )
        self.fields["project2"].queryset = Project.objects.filter(
            semester=Semester.objects.get_first_semester_with_open_registration()
        )
        self.fields["project3"].queryset = Project.objects.filter(
            semester=Semester.objects.get_first_semester_with_open_registration()
        )

    github_id = forms.IntegerField(disabled=True, label="GitHub ID")
    github_username = forms.CharField(disabled=True, label="GitHub Username")

    first_name = forms.CharField(label="First Name")
    last_name = forms.CharField(label="Last Name")

    student_number = forms.CharField(
        label="Student Number", widget=widgets.TextInput(attrs={"placeholder": "s1234567"})
    )

    course = forms.ModelChoiceField(queryset=None, empty_label=None)

    email = forms.EmailField()

    experience = forms.ChoiceField(
        label="What is your programming experience?",
        choices=Registration.EXPERIENCE_CHOICES,
        initial=Registration.EXPERIENCE_BEGINNER,
        help_text="<strong>Beginner</strong>: I passed the programming "
        "courses from my curriculum but it was not easy.<br>"
        "<strong>Intermediate</strong>: the programming courses in "
        "the curriculum were easy for me and I have experience "
        "with some small (hobby) projects.<br>"
        "<strong>Advanced</strong>: I have a lot of experience with "
        "programming.<br>"
        "<strong>NOTE</strong>: If you did not pass the programming "
        "courses and you are following the Software Engineering course, please "
        "do not register for this course.",
    )

    project1 = forms.ModelChoiceField(label="First project preference", queryset=None, required=False)

    project2 = forms.ModelChoiceField(label="Second project preference", queryset=None, required=False)

    project3 = forms.ModelChoiceField(label="Third project preference", queryset=None, required=False)

    partner1 = forms.CharField(
        label="Project partner preference",
        widget=forms.TextInput(attrs={"placeholder": "e.g. Piet Janssen"}),
        max_length=100,
        required=False,
        help_text="Optional",
    )

    partner2 = forms.CharField(
        label="Project partner preference",
        widget=forms.TextInput(attrs={"placeholder": ""}),
        max_length=100,
        required=False,
        help_text="Optional",
    )

    partner3 = forms.CharField(
        label="Project partner preference",
        widget=forms.TextInput(attrs={"placeholder": ""}),
        max_length=100,
        required=False,
        help_text="Optional",
    )

    international = forms.BooleanField(label="I don't speak Dutch", required=False)

    available_during_scheduled_timeslot_1 = forms.BooleanField(
        label="I am available during scheduled timeslot 1 for the course",
        required=False,
        initial=True,
        help_text="Timeslot 1: Monday 13:30 - 15:15",
    )

    available_during_scheduled_timeslot_2 = forms.BooleanField(
        label="I am available during scheduled timeslot 2 for the course",
        required=False,
        initial=True,
        help_text="Timeslot 2: Monday 15:30 - 17:15",
    )

    available_during_scheduled_timeslot_3 = forms.BooleanField(
        label="I am available during scheduled timeslot 3 for the course",
        required=False,
        initial=True,
        help_text="Timeslot 3: Wednesday 15:30 - 17:15",
    )

    has_problems_with_signing_an_nda = forms.BooleanField(
        label="I have problems with signing an NDA",
        required=False,
        initial=False,
        help_text="If you check this box, you will not be placed in a project that requires an NDA.",
    )

    comments = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Do you have any comments?"}),
        required=False,
        help_text="Optional",
    )

    def clean_email(self):
        """
        Check if email is already used.

        If the user has already registered, this check should pass.
        If they try to register twice, the clean method should fail.

        Some students will register with the non-existent address snumber@[student.]ru.nl.
        To save everyone a little bit of work, we block these addresses here.
        """
        if (
            User.objects.exclude(github_id=self.cleaned_data["github_id"])
            .filter(email=self.cleaned_data["email"])
            .exists()
        ):
            raise ValidationError("Email address already in use.", code="exists")

        match = wrong_email_regex.match(self.cleaned_data["email"])
        if match is not None:
            raise ValidationError("Non-existent email address.", code="invalid")

        return self.cleaned_data["email"]

    def clean_student_number(self):
        """
        Validate student number.

        If the user has already registered, this check should pass.
        If they try to register twice, the clean method should fail.
        """
        student_number = self.cleaned_data["student_number"]

        m = student_number_regex.match(student_number)
        if m is None:
            raise ValidationError("Invalid Student Number", code="invalid")

        student_number = "s" + m.group(1)

        if (
            User.objects.exclude(github_id=self.cleaned_data["github_id"])
            .filter(student_number=student_number)
            .exists()
        ):
            raise ValidationError("Student Number already in use.", code="exists")
        return student_number

    def clean(self):
        """
        Validate form variables.

        Allow existing users to register if they have not already registered in the semester.
        """
        cleaned_data = super(Step2Form, self).clean()

        if User.objects.filter(
            github_id=cleaned_data["github_id"],
            registration__semester=Semester.objects.get_first_semester_with_open_registration(),
        ).exists():
            raise ValidationError("User already registered for this semester.", code="exists")

        project1 = cleaned_data.get("project1")
        project2 = cleaned_data.get("project2")
        project3 = cleaned_data.get("project3")

        if len(set(filter(None, (project1, project2, project3)))) != 3:
            raise ValidationError("You should fill in all preferences with unique values.")
        return cleaned_data
