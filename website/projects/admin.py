import zipfile
from io import BytesIO, StringIO

from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpResponse

from projects.models import Client, Project

from registrations.models import RoleEnum

User: DjangoUser = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField with correct label."""

    def label_from_instance(self, user):
        """Get correct label."""
        return f'{user.get_full_name()}  ({user.giphouseprofile.student_number})'


# Create ModelForm based on the Group model.
class AdminProjectForm(forms.ModelForm):
    """Admin form to edit projects."""

    class Meta:
        """Meta class for AdminProjectForm."""

        model = Project
        exclude = []

    name = forms.CharField(widget=forms.TextInput)

    email = forms.EmailField(help_text="The email address that is used for the CSV export feature")

    # Add the users field.
    managers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name=RoleEnum.sdm.value),
        required=False,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('managers', False)
    )

    developers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(groups__name=RoleEnum.se.value),
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
            self.fields['managers'].initial = self.instance.user_set.filter(groups__name=RoleEnum.sdm.value)
            self.fields['developers'].initial = self.instance.user_set.filter(groups__name=RoleEnum.se.value)
            self.fields['email'].initial = self.instance.generate_email()

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
    list_filter = ['semester']
    exclude = ['permissions']
    actions = ['export_addresses_csv']

    def export_addresses_csv(self, request, queryset):
        """Export the selected projects as email CSV zip."""
        zip_content = BytesIO()
        with zipfile.ZipFile(zip_content, 'w') as zip_file:

            for project in queryset:
                content = StringIO()
                project_email = project.email
                print(
                    '"Group Email [Required]","Member Email","Member Name","Member Role","Member Type"',
                    file=content
                )
                print(f'"{project_email}","watchers@giphouse.nl","Archive GiPHouse","MEMBER","USER"', file=content)
                for user in project.user_set.all():
                    print(f'"{project_email}","{user.email}","Member","MEMBER","USER"', file=content)

                zip_file.writestr(project_email + '.csv', content.getvalue())

        response = HttpResponse(zip_content.getvalue(), content_type="application/x-zip-compressed")
        response['Content-Disposition'] = 'attachment; filename=' + 'project-addresses-export.zip'
        return response


admin.site.register(Client)
