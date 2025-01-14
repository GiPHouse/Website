from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.db.models import Q

from courses.models import Course, Semester

from projects.models import Project, Repository

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
                registration__course=Course.objects.sdm(), registration__projects=self.instance
            )

            self.fields["engineers"].initial = User.objects.filter(
                Q(registration__course=Course.objects.se()) | Q(registration__course=Course.objects.sde()),
                registration__projects=self.instance,
            )

    managers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Managers", False)
    )

    engineers = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Engineers", False)
    )

    def save_m2m(self):
        """Add the users to the Project and remove other users from the Project."""
        new_users = [*self.cleaned_data["managers"], *self.cleaned_data["engineers"]]
        for reg in Registration.objects.filter(semester=self.instance.semester, user_id__in=new_users):
            reg.projects.add(self.instance)
        for reg in Registration.objects.filter(semester=self.instance.semester, user_id__in=new_users):
            reg.projects.set([])

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance


class RepositoryInlineForm(forms.ModelForm):
    """Form for RepositoryInline."""

    def __init__(self, *args, **kwargs):
        """Limit the choices of is_archived."""
        super().__init__(*args, **kwargs)
        if self.instance is not None and self.instance.is_archived == Repository.Archived.CONFIRMED:
            self.fields["is_archived"].disabled = True
            self.fields[
                "is_archived"
            ].help_text = (
                "This repository is already archived on GitHub. It is currently not possible to unarchive them."
            )
        else:
            self.fields["is_archived"].choices = Repository.Archived.choices[:-1]
            self.fields[
                "is_archived"
            ].help_text = "Setting this to 'To be archived' will archive this repository during the next GitHub sync."
