from django.urls import path

from github_oauth.views import GithubLoginView, GithubRegisterView

app_name = 'github_oauth'
urlpatterns = [
    path('login/', GithubLoginView.as_view(), name='login'),
    path('register/', GithubRegisterView.as_view(), name='register')
]
