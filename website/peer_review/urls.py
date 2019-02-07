from django.contrib import admin
from django.urls import path

from .views import *
app_name = 'peer_review'

urlpatterns = [
    path('', show_form, name = 'show'),
    path('submit', submit_form, name = 'submit'),
]
