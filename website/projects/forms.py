from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.text import slugify
from django.core.exceptions import ValidationError

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
        # widgets = {
        #     "users": forms.HiddenInput(),
        # }

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        self.fields["managers"].queryset = User.objects.filter(
            registration__course=Course.objects.sdm(),
            registration__semester=Semester.objects.get_or_create_current_semester(),
        )

        self.fields["engineers"].queryset = User.objects.filter(
            Q(registration__course=Course.objects.se())
            | Q(registration__course=Course.objects.sde()),
            registration__semester=Semester.objects.get_or_create_current_semester(),
        )

        if self.instance.pk:
            self.fields["managers"].initial = User.objects.filter(
                registration__course=Course.objects.sdm(),
                registration__projects=self.instance,
            )

            self.fields["engineers"].initial = User.objects.filter(
                Q(registration__course=Course.objects.se())
                | Q(registration__course=Course.objects.sde()),
                registration__projects=self.instance,
            )

    managers = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=widgets.FilteredSelectMultiple("Managers", False),
    )

    engineers = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=widgets.FilteredSelectMultiple("Engineers", False),
    )

    class Media:
        js = ("admin/js/admin.js",)

    def clean(self):
        """Validate form data and handle semester changes."""
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        semester = cleaned_data.get("semester")

        if semester and name:
            expected_slug = slugify(f"{name}-{semester.year}")

            existing_project = Project.objects.filter(
                slug=expected_slug
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            if existing_project.exists():
                raise ValidationError(
                    f'A project with slug "{expected_slug}" already exists please choose a different name'
                )

    def save_m2m(self):
        """Add the users to the Project and remove other users from the Project."""
        new_users = [
            *self.cleaned_data["managers"],
            *self.cleaned_data["engineers"],
        ]
        for reg in Registration.objects.filter(
            semester=self.instance.semester, user_id__in=new_users
        ):
            reg.add_project(self.instance)
        for reg in Registration.objects.filter(
            semester=self.instance.semester, user_id__in=new_users
        ):
            reg.remove_projects()

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance


class NewRepositoryInlineForm(forms.ModelForm):
    """Form for NewRepositoryInline."""

    def __init__(self, *args, **kwargs):
        """Limit the choices of is_archived."""
        super().__init__(*args, **kwargs)

        self.fields["is_archived"].choices = Repository.Archived.choices[:-1]
        self.fields[
            "is_archived"
        ].help_text = "Setting this to 'To be archived' will archive this repository during the next GitHub sync."


class ExistingRepositoryInlineForm(forms.ModelForm):
    """Form for ExistingRepositoryInline."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[
            "github_repo_id"
        ].help_text = "Pasting the repository id is recommended because when a repository is fetched this field can not be altered anymore."

        # Limit the choices of is_archived.
        if self.instance and self.instance.pk:  # existing obj
            if self.instance.is_archived == Repository.Archived.CONFIRMED:
                self.fields["is_archived"].disabled = True
                self.fields[
                    "is_archived"
                ].help_text = "This repository is already archived on GitHub. It is currently not possible to unarchive them."
            else:
                self.fields[
                    "is_archived"
                ].choices = Repository.Archived.choices[:-1]
                self.fields[
                    "is_archived"
                ].help_text = "Setting this to 'To be archived' will archive this repository during the next GitHub sync."

        # Set other fields' statuses (on/off) and help texts.
        if self.instance and self.instance.pk:  # existing obj
            self.fields["github_repo_id"].disabled = True
            self.fields[
                "github_repo_id"
            ].help_text = "This is the id of the GitHub repository."

        self.fields["github_repo_id"].widget.attrs["class"] = (
            "github_repo_id-field"
        )
