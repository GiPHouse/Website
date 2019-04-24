from django.urls import path

from peer_review.views import OverviewView, PeerReviewView

app_name = 'peer_review'

urlpatterns = [
    path('', OverviewView.as_view(), name='overview'),
    path('<int:questionnaire>', PeerReviewView.as_view(), name='answer')
]
