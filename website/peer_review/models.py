from django.db import models
from django.contrib.auth.models import User

PoorGoodScale = ("Very poor", "Poor", "Average", "Good", "Very good")

AgreeDisagreeScale = ("Strongly disagree", "Disagree",
                      "Neutral", "Agree", "Strongly agree")

POOR_GOOD_SCALE = [(x, x) for x in PoorGoodScale]
AGREE_DISAGREE_SCALE = [(x, x) for x in AgreeDisagreeScale]


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
        if self.question_type == 'p':
            return PoorGoodScale
        if self.question_type == 'a':
            return AgreeDisagreeScale
        return []

    def closed_question(self):
        return self.question_type in ['p', 'a']

    def choices(self):
        if not self.closed_question():
            return False

        if self.question_type == 'p':
            return POOR_GOOD_SCALE
        elif self.question_type == 'a':
            return AGREE_DISAGREE_SCALE

        return ()


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
        related_name='peer')

    def __str__(self):
        return '({} → {}) {}'.format(self.participant, self.peer, self.answer)
