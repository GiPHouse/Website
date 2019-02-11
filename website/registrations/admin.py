from django import forms
from django.contrib import admin
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from .models import Project, Semester, GiphouseProfile, RoleChoice

User = get_user_model()


class UserModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, user):
        return f'{user.first_name} {user.last_name} (s{user.giphouseprofile.snumber})'


# Create ModelForm based on the Group model.
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        exclude = []

    name = forms.CharField(widget=forms.TextInput)

    # Add the users field.
    managers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(giphouseprofile__role=RoleChoice.sdm.name),
        required=True,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('managers', False)
    )

    developers = UserModelMultipleChoiceField(
        queryset=User.objects.filter(giphouseprofile__role=RoleChoice.se.name),
        required=True,
        # Use the pretty 'filter_horizontal widget'.
        widget=widgets.FilteredSelectMultiple('developers', False)
    )

    def __init__(self, *args, **kwargs):
        # Do the normal form initialisation.
        super(ProjectForm, self).__init__(*args, **kwargs)
        # If it is an existing group (saved objects have a pk).
        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['managers'].initial = self.instance.user_set.filter(giphouseprofile__role=RoleChoice.sdm.name)
            self.fields['developers'].initial = self.instance.user_set.filter(giphouseprofile__role=RoleChoice.se.name)

    def save_m2m(self):
        # Add the users to the Group.
        self.instance.user_set.set([*self.cleaned_data['managers'], *self.cleaned_data['developers']])

    def save(self, *args, **kwargs):
        # Default save
        instance = super(ProjectForm, self).save()
        # Save many-to-many data
        self.save_m2m()
        return instance


class ProjectAdmin(admin.ModelAdmin):
    form = ProjectForm
    exclude = ['permissions']


class GiphouseProfileForm(forms.ModelForm):
    github_username = forms.CharField(widget=forms.TextInput)


class GiphouseProfileInline(admin.StackedInline):
    model = GiphouseProfile
    form = GiphouseProfileForm


class Student(User):
    class Meta:
        proxy = True

    @property
    def github_username(self):
        return self.giphouseprofile.github_username


class StudentAdmin(admin.ModelAdmin):
    inlines = [GiphouseProfileInline]
    list_display = ('first_name', 'last_name', 'github_username')
    fields = ('first_name', 'last_name', 'email', 'date_joined', 'groups', 'user_permissions')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user_permissions':
            kwargs["queryset"] = Permission.objects.filter()
        return super(StudentAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        return self.model.objects.filter(giphouseprofile__isnull=False)


admin.site.register(Student, StudentAdmin)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Semester)
