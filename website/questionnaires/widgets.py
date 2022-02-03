from django.forms.widgets import ChoiceWidget


class ButtonGroupWidget(ChoiceWidget):
    """A RadioSelect that renders as a horizontal button groep."""

    template_name = "questionnaires/widgets/button_group.html"
