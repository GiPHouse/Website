import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError
from django.forms import widgets

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import GiphouseProfile, Registration, Student

student_number_regex = re.compile(r"^[sS]?(\d{7})$")
User: DjangoUser = get_user_model()


class Step2Form(forms.Form):
    """Form to get user information for registration."""

    def __init__(self, *args, **kwargs):
        """Set querysets dynamically."""
        super().__init__(*args, **kwargs)

        self.fields["course"].queryset = Course.objects.all()

        self.fields["project1"].queryset = Project.objects.filter(semester=Semester.objects.get_current_semester())
        self.fields["project2"].queryset = Project.objects.filter(semester=Semester.objects.get_current_semester())
        self.fields["project3"].queryset = Project.objects.filter(semester=Semester.objects.get_current_semester())

    first_name = forms.CharField(widget=widgets.TextInput(attrs={"class": "form-control"}))
    last_name = forms.CharField()

    student_number = forms.CharField(
        label="Student Number", widget=widgets.TextInput(attrs={"placeholder": "s1234567"})
    )
    github_username = forms.CharField(disabled=True)

    course = forms.ModelChoiceField(queryset=None, empty_label=None)

    email = forms.EmailField()

    experience = forms.ChoiceField(
        label="What is your programming experience?",
        choices=Registration.EXPERIENCE_CHOICES,
        initial=Registration.EXPERIENCE_BEGINNER,
    )

    project1 = forms.ModelChoiceField(label="First project preference", queryset=None)

    project2 = forms.ModelChoiceField(label="Second project preference", queryset=None)

    project3 = forms.ModelChoiceField(label="Third project preference", queryset=None)

    comments = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Who do you want to work with? \n" "Any other comments?"}),
        help_text="Optional",
        required=False,
    )

    def clean(self):
        """Validate form variables."""
        cleaned_data = super(Step2Form, self).clean()

        project1 = cleaned_data.get("project1")
        project2 = cleaned_data.get("project2")
        project3 = cleaned_data.get("project3")

        if len(set(filter(None, (project1, project2, project3)))) != 3:
            raise ValidationError("You should fill in all preferences with unique values.")
        return cleaned_data

    def clean_email(self):
        """Check if email is already used."""
        if User.objects.filter(email=self.cleaned_data["email"]).exists():
            raise ValidationError("Email already in use", code="exists")
        return self.cleaned_data["email"]

    def clean_student_number(self):
        """Validate student number."""
        student_number = self.cleaned_data["student_number"]

        m = student_number_regex.match(student_number)
        if m is None:
            raise ValidationError("Invalid Student Number", code="invalid")

        student_number = "s" + m.group(1)

        if GiphouseProfile.objects.filter(student_number=student_number).exists():
            ValidationError("Student Number already in use", code="exists")

        return student_number


class StudentAdminForm(forms.ModelForm):
    """Admin form to edit Students."""

    class Meta:
        """Meta class for StudentForm."""

        model = Student
        fields = ("first_name", "last_name", "email", "date_joined")
        exclude = []

    project = forms.ModelChoiceField(queryset=Project.objects.all(), required=False)

    def __init__(self, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        self.fields["project"].initial = Project.objects.filter(user=self.instance).first()

        user_registration = self.instance.registration_set.order_by("-semester").first()
        if user_registration is not None:
            self.fields["project"].queryset = Project.objects.filter(semester=user_registration.semester)

    def save_m2m(self):
        """Add the user to the specified groups."""
        groups = []
        project = self.cleaned_data["project"]
        if project:
            groups.append(project)
        self.instance.groups.set(groups)

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance
