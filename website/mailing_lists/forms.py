from django import forms
from django.utils.html import escape

from giphousewebsite.settings.base import GSUITE_DOMAIN

from mailing_lists.models import MailingList


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


class AddressSuffixedForm(forms.ModelForm):
    """ModelForm for forms where the address field should be suffixed."""

    class Meta:
        """Meta class for AddressSuffixedForm."""

        model = MailingList
        fields = "__all__"
        widgets = {"address": SuffixTextInputWidget(suffix=f"@{GSUITE_DOMAIN}")}
