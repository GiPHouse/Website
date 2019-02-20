from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, get_list_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic.edit import FormView

from .models import *
from .forms import PeerReviewForm

class PeerReviewView(FormView):
    template_name = 'peer_review_form.html'
    form_class = PeerReviewForm
    def get_form(self, form_class=None):
        """Return an instance of the form to be used in this view."""
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.request.user,**self.get_form_kwargs())
    
    def form_valid(self, form):
        participant = self.request.user
        peers = User.objects.exclude(pk=participant.pk)
        questions = Question.objects.all()
 
        for q in questions:
            if q.about_someone_else:
                for peer in peers:
                    a = Answer()
                    a.participant = participant
                    a.peer = peer
                    a.question = q
                    a.answer = form.cleaned_data[f"{peer.username}_{q.pk}"]
                    a.save()
            else:
                a = Answer()
                a.participant = participant
                a.peer = peer
                a.question = q
                a.answer = form.cleaned_data[f"{q.pk}"]
                a.save()
                
        messages.success(self.request, "Peer review succesfully submitted!")
        return redirect("home")

#@login_required
def show_form(request):
    global_questions = Question.objects.filter(about_someone_else=False)
    peer_questions = Question.objects.filter(about_someone_else=True)

    #TODO only show users in your group
    peers = User.objects.all()

    context = {
        'global_questions' : global_questions,
        'peer_questions': peer_questions,
        'peers' : peers,
    }
    return render(request, 'peer_review.html', context)

def submit_form(request):
    #TODO error handling
    #TODO input validation
    participant = request.user

    #TODO only show users in your group
    peers = User.objects.all()
    
    questions = Question.objects.all()
    answers = []
    for q in questions:
        if q.about_someone_else:
            for peer in peers:
                a = Answer()
                a.participant = participant
                a.peer = peer
                a.question = q
                a.answer = request.POST[f"{peer.username}-{q.pk}"]
                a.save()
        else:
            a = Answer()
            a.participant = participant
            a.peer = peer
            a.question = q
            a.answer = request.POST[str(q.pk)]
            a.save()
    messages.success(request, "Peer review succesfully submitted!")
    return redirect("home")
