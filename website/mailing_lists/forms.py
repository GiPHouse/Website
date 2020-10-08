from django import forms
from django.conf import settings
from django.contrib.admin import widgets
from django.contrib.auth import get_user_model
from django.utils.html import escape

from courses.models import Semester

from mailing_lists.models import MailingList

from registrations.models import Employee

User: Employee = get_user_model()


class SuffixTextInputWidget(forms.TextInput):
    """An input widget that appends supplied text to the regular text input widget's rendered html."""

    def __init__(self, attrs=None, suffix=""):
        """
        Create widget with supplied suffixes.

        :param attrs: Widget attributes
        :param suffix: Suffix to add at the end of the render output
        """
        self.suffix = escape(suffix)
        super().__init__(attrs)

    def render(self, name, value, attrs=None, renderer=None):
        """Render the widget."""
        html = super().render(name, value, attrs, renderer)
        html += self.suffix
        return html


class MailingListAdminForm(forms.ModelForm):
    """ModelForm to search users in userlist of a mailinglist."""

    class Meta:
        """Meta class for MailingListAdminForm."""

        model = MailingList
        exclude = []
        fields = "__all__"
        widgets = {"address": SuffixTextInputWidget(suffix=f"@{settings.GSUITE_DOMAIN}")}

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        super().__init__(*args, **kwargs)

        self.fields["users"].queryset = User.objects.filter(
            registration__semester=Semester.objects.get_or_create_current_semester(),
        )

    users = forms.ModelMultipleChoiceField(
        queryset=None, required=False, widget=widgets.FilteredSelectMultiple("Users", False)
    )

    def save_m2m(self):
        """Add the users to the Mailinglist and remove other users from the Mailinglist."""
        self.clean()

    def save(self, *args, **kwargs):
        """Save the form data, including many-to-many data."""
        instance = super().save()
        self.save_m2m()
        return instance
