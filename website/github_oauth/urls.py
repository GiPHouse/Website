from django.urls import path
from django.views.defaults import page_not_found

from .views import github_login, github_register

app_name = 'github_oauth'
urlpatterns = [
    path('', page_not_found,  name='oauth'),
    path('login/', github_login, name='login'),
    path('register/', github_register, name='register')
]
