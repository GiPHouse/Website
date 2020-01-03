from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.db.models import Q

from courses.models import Course, Semester

from projects.models import Project

from registrations.models import Employee, Registration

User: Employee = get_user_model()


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
            registration__course=Course.objects.sdm(),
            registration__semester=Semester.objects.get_or_create_current_semester(),
        )

        self.fields["engineers"].queryset = User.objects.filter(
            Q(registration__course=Course.objects.se()) | Q(registration__course=Course.objects.sde()),
            registration__semester=Semester.objects.get_or_create_current_semester(),
        )

        if self.instance.pk:
            self.fields["managers"].initial = User.objects.filter(
                registration__course=Course.objects.sdm(), registration__project=self.instance
            )

            self.fields["engineers"].initial = User.objects.filter(
                Q(registration__course=Course.objects.se()) | Q(registration__course=Course.objects.sde()),
                registration__project=self.instance,
            )

    email = forms.EmailField(help_text="The email address that is used for the CSV export feature", required=False)

    managers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Managers", False)
    )

    engineers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Engineers", False)
    )

    def save_m2m(self):
        """Add the users to the Project and remove other users from the Project."""
        new_users = [*self.cleaned_data["managers"], *self.cleaned_data["engineers"]]
        Registration.objects.filter(semester=self.instance.semester, user_id__in=new_users).update(
            project=self.instance
        )
        Registration.objects.filter(project=self.instance).exclude(user_id__in=new_users).update(project=None)

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance
