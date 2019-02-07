from django.db import models
from django.contrib.auth.models import User

class Question(models.Model):
    question = models.CharField(max_length=200)
    closed_question = models.BooleanField(default=False)

    def __str__(self):
        return str(self.question)

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answer = models.CharField(max_length=200)
    participant = models.ForeignKey(User, on_delete=models.CASCADE, related_name='participant')
    peer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='peer')
    
    def __str__(self):
        return '({} → {}) {}'.format(self.participant,self.peer, self.answer)
