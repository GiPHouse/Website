from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth import get_user_model

from projects.models import Project, Client
from registrations.models import RoleChoice

User: DjangoUser = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField with correct label."""

    def label_from_instance(self, user):
        """Get correct label."""
        return f'{user.first_name} {user.last_name} ({user.giphouseprofile.student_number})'


# Create ModelForm based on the Group model.
class ProjectForm(forms.ModelForm):
    """Admin form to edit projects."""

    class Meta:
        """Meta class for ProjectForm."""

        model = Project
        exclude = []

    name = forms.CharField(widget=forms.TextInput)

    # Add the users field.
    managers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(giphouseprofile__role=RoleChoice.sdm.name),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('managers', False)
    )

    developers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(giphouseprofile__role=RoleChoice.se.name),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('developers', False)
    )

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        # Do the normal form initialisation.
        super(ProjectForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['managers'].initial = self.instance.user_set.filter(giphouseprofile__role=RoleChoice.sdm.name)
            self.fields['developers'].initial = self.instance.user_set.filter(giphouseprofile__role=RoleChoice.se.name)

    def save_m2m(self):
        """Add the users to the Group."""
        self.instance.user_set.set([*self.cleaned_data['managers'], *self.cleaned_data['developers']])

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super(ProjectForm, self).save()
        self.save_m2m()
        return instance


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = ProjectForm
    exclude = ['permissions']


admin.site.register(Client)
