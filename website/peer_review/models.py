from django.db import models
from django.contrib.auth.models import User
from enum import Enum

from django.utils import timezone


class ScaleLabels(Enum):
    """Possible answer scales."""

    poor_good = ("Very poor", "Poor", "Average", "Good", "Very good")
    agree_disagree = ("Strongly disagree", "Disagree",
                      "Neutral", "Agree", "Strongly agree")


SCALE_LABEL_CHOICES = {
    tag.name: [(y, y) for y in tag.value]
    for tag in ScaleLabels
}


class QuestionTypes(Enum):
    """Possible question types."""

    poor_good = 'Poor/Good Likert Scale'
    agree_disagree = 'Agree/Disagree Likert Scale'
    open_question = 'Open Question'


class QuestionnaireManager(models.Manager):
    """Manager for the Questionnaire model."""

    def open_questionnaires(self):
        """Return the questionnaires that are available at the current time."""
        return self.filter(available_from__lte=timezone.now(),
                           available_until__gte=timezone.now())


class Questionnaire(models.Model):
    """A group of questions."""

    title = models.CharField(max_length=200)
    available_from = models.DateTimeField()
    available_until = models.DateTimeField()

    objects = QuestionnaireManager()

    def __str__(self):
        """Return title."""
        return self.title


class Question(models.Model):
    """Question model."""

    questionnaire = models.ForeignKey(Questionnaire, null=True, on_delete=models.SET_NULL)
    question = models.CharField(max_length=200)
    question_type = models.CharField(
        max_length=20,
        choices=[(tag.name, tag.value) for tag in QuestionTypes]
    )
    about_team_member = models.BooleanField(default=False)

    def get_scale_labels(self):
        """Get scale labels."""
        return ScaleLabels[self.question_type].value

    def closed_question(self):
        """Return whether a question is closed."""
        return QuestionTypes[self.question_type] in [
            QuestionTypes.poor_good,
            QuestionTypes.agree_disagree
        ]

    def choices(self):
        """Get choices."""
        return SCALE_LABEL_CHOICES[self.question_type]

    def __str__(self):
        """Return question string."""
        return str(self.question)


class Answer(models.Model):
    """An answer to a question."""

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participant'
    )
    peer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='peer',
        blank=True,
        null=True
    )
    created = models.DateTimeField(
        auto_now_add=True,
    )
    on_time = models.BooleanField()

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """Save model and set on_time field."""
        if self.created:
            self.on_time = self.created < self.question.questionnaire.available_until
        else:
            self.on_time = timezone.now() < self.question.questionnaire.available_until
        super().save(force_insert, force_update, using, update_fields)

    def __str__(self):
        """Return information about answer as string."""
        return f'({self.participant} about {self.peer}) {self.question}:  answer {self.answer}'
