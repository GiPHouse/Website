from django.urls import path

from .views import PeerReviewView, OverviewView

app_name = 'peer_review'

urlpatterns = [
    path('', OverviewView.as_view(), name='overview'),
    path('<int:questionnaire>', PeerReviewView.as_view(), name='answer')
]
