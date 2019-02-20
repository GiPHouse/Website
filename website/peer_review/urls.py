from django.contrib import admin
from django.urls import path

from .views import *
app_name = 'peer_review'

urlpatterns = [
    path('', show_form, name = 'show'),
    path('form', PeerReviewView.as_view(), name = 'form'),
    path('submit', submit_form, name = 'submit'),
]
