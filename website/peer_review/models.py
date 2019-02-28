from django.db import models
from django.contrib.auth.models import User

SCALE_LABELS = {
    'p': ("Very poor", "Poor", "Average", "Good", "Very good"),
    'a': ("Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"),
}

SCALE_LABEL_CHOICES = {
    x: [(y, y) for y in SCALE_LABELS[x]]
    for x in SCALE_LABELS
}

QUESTION_TYPES = (
    ('p', 'Poor/Good Likert Scale'),
    ('a', 'Agree/Disagree Likert Scale'),
    ('o', 'Open Question'),
)


class Question(models.Model):
    question = models.CharField(max_length=200)
    question_type = models.CharField(max_length=1, choices=QUESTION_TYPES)
    about_someone_else = models.BooleanField(default=False)

    def __str__(self):
        return str(self.question)

    def get_scale_labels(self):
        return SCALE_LABELS[self.question_type]

    def closed_question(self):
        return self.question_type in ['p', 'a']

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
        return '({} → {}) {}'.format(self.participant, self.peer, self.answer)
