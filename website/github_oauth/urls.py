from django.urls import path

from github_oauth.views import github_login, github_register

app_name = 'github_oauth'
urlpatterns = [
    path('login/', github_login, name='login'),
    path('register/', github_register, name='register')
]
