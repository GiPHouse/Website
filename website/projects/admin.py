from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser

from projects.models import Client, Project

from projects.models import Client, Project

User: DjangoUser = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField with correct label."""

    def label_from_instance(self, user):
        """Get correct label."""
        return f'{user.first_name} {user.last_name} ({user.giphouseprofile.student_number})'


# Create ModelForm based on the Group model.
class AdminProjectForm(forms.ModelForm):
    """Admin form to edit projects."""

    class Meta:
        """Meta class for AdminProjectForm."""

        model = Project
        exclude = []

    name = forms.CharField(widget=forms.TextInput)

    # Add the users field.
    managers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='SDM Student'),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('managers', False)
    )

    developers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name='SE Student'),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('developers', False)
    )

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['managers'].initial = self.instance.user_set.filter(groups__name='SDM Student')
            self.fields['developers'].initial = self.instance.user_set.filter(groups__name='SE Student')

    def save_m2m(self):
        """Add the users to the Group."""
        self.instance.user_set.set([*self.cleaned_data['managers'], *self.cleaned_data['developers']])

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Custom admin for projects."""

    form = AdminProjectForm
    exclude = ['permissions']


admin.site.register(Client)
