from django import forms


class PeerReviewForm(forms.Form):
    """Dynamic form generating a peer review form."""

    def __init__(self, peers=None, questions=None, *args, **kwargs):
        """Dynamically setup form."""
        super().__init__(*args, **kwargs)

        for question in questions:
            if question.about_team_member:
                for peer in peers:
                    field_name = f"{peer.username}_{question.pk}"
                    self._build_form_field(question, field_name, peer)
            else:
                field_name = f"{question.pk}"
                self._build_form_field(question, field_name)

    def _build_form_field(self, question, field_name, peer=None):
        if question.closed_question():
            self.fields[field_name] = forms.ChoiceField(
                label=question.question,
                widget=forms.RadioSelect(attrs={'class': 'multiple-choice'}),
                choices=question.choices(),
            )
        else:
            self.fields[field_name] = forms.CharField(label=question.question,)

        if question.about_team_member and peer is not None:
            self.fields[field_name].help_text = f"Peer review for {peer.first_name} {peer.last_name}"
        else:
            self.fields[field_name].help_text = "General Questions"
