from django.shortcuts import render
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

from .models import *

#@login_required
def show_form(request):
    questions = Question.objects.all()

    #TODO only show users in your group
    peers = User.objects.all()

    context = {
        'questions': questions,
        'peers' : peers,
    }
    return render(request, 'peer_review.html', context)

def submit_form(request):
    #TODO error handling
    #TODO input validation
    participant = request.user
    peer = User.objects.get(username=request.POST['peer'])
    
    questions = Question.objects.all()
    answers = []
    for q in questions:
        a = Answer()
        a.participant = participant
        a.peer = peer
        a.question = q
        a.answer = request.POST[str(q.pk)]
        a.save()
    return render(request, 'succes.html', {})
