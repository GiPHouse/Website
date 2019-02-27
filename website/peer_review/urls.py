from django.urls import path

from .views import PeerReviewView

app_name = 'peer_review'

urlpatterns = [
    path('', PeerReviewView.as_view(), name='show'),
]
