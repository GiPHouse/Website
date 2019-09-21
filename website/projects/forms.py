from django import forms
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser

from projects.models import Project

from registrations.models import Role

User: DjangoUser = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField with correct label."""

    def label_from_instance(self, user):
        """Get correct label."""
        return f"{user.get_full_name()}  ({user.giphouseprofile.student_number})"


class ProjectAdminForm(forms.ModelForm):
    """Admin form to edit projects."""

    class Meta:
        """Meta class for AdminProjectForm."""

        model = Project
        exclude = []

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        # Check if this is an existing Project
        if self.instance.pk:
            self.fields["managers"].initial = self.instance.user_set.all()
            self.fields["developers"].initial = self.instance.user_set.all()

    name = forms.CharField(widget=forms.TextInput)

    email = forms.EmailField(help_text="The email address that is used for the CSV export feature", required=False)

    managers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name=Role.SDM),
        required=False,
        widget=widgets.FilteredSelectMultiple("managers", False),
    )

    developers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name=Role.SE),
        required=False,
        widget=widgets.FilteredSelectMultiple("developers", False),
    )

    def save_m2m(self):
        """Add the users to the Group."""
        self.instance.user_set.set([*self.cleaned_data["managers"], *self.cleaned_data["developers"]])

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance
