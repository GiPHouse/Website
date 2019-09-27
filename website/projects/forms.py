from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.db.models import Q

from courses.models import Course, Semester

from projects.models import Project

User: DjangoUser = get_user_model()


class ProjectAdminForm(forms.ModelForm):
    """Admin form to edit projects."""

    class Meta:
        """Meta class for AdminProjectForm."""

        model = Project
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        self.fields["managers"].queryset = User.objects.filter(
            registration__course=Course.objects.sdm(), registration__semester=Semester.objects.get_current_semester()
        )

        self.fields["engineers"].queryset = User.objects.filter(
            Q(registration__course=Course.objects.se()) | Q(registration__course=Course.objects.sde()),
            registration__semester=Semester.objects.get_current_semester(),
        )

        if self.instance.pk:
            self.fields["managers"].initial = User.objects.filter(registration__course=Course.objects.sdm())

            self.fields["engineers"].initial = User.objects.filter(
                Q(registration__course=Course.objects.se()) | Q(registration__course=Course.objects.sde())
            )

    name = forms.CharField(widget=forms.TextInput)

    email = forms.EmailField(help_text="The email address that is used for the CSV export feature", required=False)

    managers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Managers", False)
    )

    engineers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Engineers", False)
    )

    def save_m2m(self):
        """Add the users to the Group."""
        self.instance.user_set.set([*self.cleaned_data["managers"], *self.cleaned_data["engineers"]])

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance
