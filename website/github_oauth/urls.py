from django.urls import path

from .views import github_callback

app_name = 'github_oauth'
urlpatterns = [
    path('callback/', github_callback, name='callback'),
]
