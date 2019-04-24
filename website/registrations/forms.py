import re

from courses.models import Semester

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.core.exceptions import ValidationError
from django.forms import widgets

from projects.models import Project

from registrations.models import GiphouseProfile, RoleChoice

student_number_regex = re.compile(r'^[sS]?(\d{7})$')
User: DjangoUser = get_user_model()


class Step2Form(forms.Form):
    """Form to get user information for registration."""

    def __init__(self, *args, **kwargs):
        """Set querysets dynamically."""
        super().__init__(*args, **kwargs)
        self.fields['project1'].queryset = Project.objects.filter(semester=Semester.objects.get_current_registration())
        self.fields['project2'].queryset = Project.objects.filter(semester=Semester.objects.get_current_registration())
        self.fields['project3'].queryset = Project.objects.filter(semester=Semester.objects.get_current_registration())

    first_name = forms.CharField(widget=widgets.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField()

    student_number = forms.CharField(
        label="Student Number",
        widget=widgets.TextInput(attrs={'placeholder': "s1234567"}))
    github_username = forms.CharField(disabled=True)

    course = forms.ChoiceField(choices=(('', '---------'),
                                        (RoleChoice.se.name, 'Software Engineering'),
                                        (RoleChoice.sdm.name, 'System Development Management')))

    email = forms.EmailField()

    project1 = forms.ModelChoiceField(
        label="First project preference",
        queryset=None,
    )

    project2 = forms.ModelChoiceField(
        label="Second project preference",
        help_text="Optional",
        required=False,
        queryset=None,
    )

    project3 = forms.ModelChoiceField(
        label="Third project preference",
        help_text="Optional",
        required=False,
        queryset=None,
    )

    comments = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Who do you want to work with? \n"
                                                                           "Any other comments?"}),
                               help_text="Optional",
                               required=False)

    def clean(self):
        """Validate form variables."""
        cleaned_data = super(Step2Form, self).clean()

        project1 = cleaned_data['project1']
        project2 = cleaned_data.get('project2')
        project3 = cleaned_data.get('project3')

        if ((project2 and project2 == project1)
                or (project3 and project3 == project1)
                or (project3 and project2 and project2 == project3)):
            raise ValidationError("The same project has been selected multiple times.")

        return cleaned_data

    def clean_email(self):
        """Check if email is already used."""
        if User.objects.filter(email=self.cleaned_data['email']).exists():
            raise ValidationError("Email already in use", code='exists')
        return self.cleaned_data['email']

    def clean_student_number(self):
        """Validate student number."""
        student_number = self.cleaned_data['student_number']

        m = student_number_regex.match(student_number)
        if m is None:
            raise ValidationError("Invalid Student Number", code='invalid')

        student_number = 's' + m.group(1)

        if GiphouseProfile.objects.filter(student_number=student_number).exclude():
            ValidationError("Student Number already in use", code='exists')

        return student_number
