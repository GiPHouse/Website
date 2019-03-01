from django.db import models
from django.contrib.auth.models import User
from enum import Enum


class ScaleLabels(Enum):
    poorGood = ("Very poor", "Poor", "Average", "Good", "Very good")
    agreeDisagree = ("Strongly disagree", "Disagree",
                     "Neutral", "Agree", "Strongly agree")


SCALE_LABEL_CHOICES = {
    tag.name: [(y, y) for y in tag.value]
    for tag in ScaleLabels
}


class QuestionTypes(Enum):
    poorGood = 'Poor/Good Likert Scale'
    agreeDisagree = 'Agree/Disagree Likert Scale'
    openQuestion = 'Open Question'


class Question(models.Model):
    question = models.CharField(max_length=200)
    question_type = models.CharField(
        max_length=20, choices=[(tag.name, tag.value) for tag in QuestionTypes])
    about_team_member = models.BooleanField(default=False)

    def __str__(self):
        return str(self.question)

    def get_scale_labels(self):
        return ScaleLabels[self.question_type].value

    def closed_question(self):
        return self.question_type in [
            QuestionTypes.poorGood.name,
            QuestionTypes.agreeDisagree.name
        ]

    def choices(self):
        return SCALE_LABEL_CHOICES[self.question_type]


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    participant = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='participant')
    peer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='peer', blank=True, null=True)

    def __str__(self):
        return '({} about {}) {}:  answer {}'.format(
            self.participant,
            self.peer,
            self.question,
            self.answer
        )
