import re

from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.forms import widgets

from registrations.models import RoleChoice, Project, Semester, GiphouseProfile

student_number_regex = re.compile(r'^[sS]?(\d{7})$')
User = get_user_model()


class Step2Form(forms.Form):
    first_name = forms.CharField(widget=widgets.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField()

    student_number = forms.CharField(label="Student Number", widget=widgets.TextInput(attrs={'placeholder': "s1234567"}))
    github_username = forms.CharField(disabled=True)

    course = forms.ChoiceField(choices=(('', '---------'),
                                        (RoleChoice.se.name, 'Software Engineering'),
                                        (RoleChoice.sdm.name, 'System Development Management')))

    email = forms.EmailField()

    project1 = forms.ModelChoiceField(label="First project preference",
                                      queryset=Project.objects.filter(
                                          semester=Semester.objects.get_current_registration()))

    project2 = forms.ModelChoiceField(label="Second project preference",
                                      help_text="Optional",
                                      required=False,
                                      queryset=Project.objects.filter(
                                          semester=Semester.objects.get_current_registration()))

    project3 = forms.ModelChoiceField(label="Third project preference",
                                      help_text="Optional",
                                      required=False,
                                      queryset=Project.objects.filter(
                                          semester=Semester.objects.get_current_registration()))

    comments = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Who do you want to work with? \n"
                                                                           "Any other comments?"}),
                               help_text="Optional",
                               required=False)

    def clean(self):
        cleaned_data = super(Step2Form, self).clean()

        try:
            User.objects.get(email=cleaned_data['email'])
        except User.DoesNotExist:
            pass
        else:
            ValidationError("Email already in use", code='exists')

        try:
            GiphouseProfile.objects.get(student_number=cleaned_data['student_number'])
        except GiphouseProfile.DoesNotExist:
            pass
        else:
            ValidationError("Student Number already in use", code='exists')

        project1 = cleaned_data['project1']
        project2 = cleaned_data.get('project2')
        project3 = cleaned_data.get('project3')

        if ((project2 and project2 == project1)
                or (project3 and project3 == project1)
                or (project3 and project2 and project2 == project3)):
            raise ValidationError("The same project has been selected multiple times.")

    def clean_student_number(self):
        student_number = self.cleaned_data['student_number']

        m = student_number_regex.match(student_number)
        if m is None:
            raise ValidationError("Invalid Student Number", code='invalid')

        return 's' + m.group(1)
