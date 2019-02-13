import re

from django import forms
from django.core.exceptions import ValidationError
from django.forms import widgets

from registrations.models import RoleChoice, Project, Semester

s_number_regex = re.compile(r'^[sS]?(\d{7})$')


class Step2Form(forms.Form):
    first_name = forms.CharField(widget=widgets.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField()

    s_number = forms.CharField(label="Student Number", widget=widgets.TextInput(attrs={'placeholder': "s1234567"}))
    github_username = forms.CharField(disabled=True)

    course = forms.ChoiceField(choices=(('', '---------'),
                                        (RoleChoice.se.name, 'Software Engineering'),
                                        (RoleChoice.sdm.name, 'System Development Management')))

    email = forms.EmailField()

    project1 = forms.ModelChoiceField(label="First project preference",
                                      queryset=Project.objects.filter(semester=Semester.objects.get_current()))

    project2 = forms.ModelChoiceField(label="Second project preference",
                                      help_text="Optional",
                                      required=False,
                                      queryset=Project.objects.filter(semester=Semester.objects.get_current()))

    project3 = forms.ModelChoiceField(label="Third project preference",
                                      help_text="Optional",
                                      required=False,
                                      queryset=Project.objects.filter(semester=Semester.objects.get_current()))

    comments = forms.CharField(widget=forms.Textarea(attrs={'placeholder': "Who do you want to work with?\n"
                                                                           "Any other comments?"}),
                               help_text="Optional",
                               required=False)

    def clean_s_number(self):
        s_number = self.cleaned_data['s_number']

        m = s_number_regex.match(s_number)
        if m is None:
            raise ValidationError("not a valid s number")
        return m.group(1)
