from django.urls import path

from .views import show

app_name = 'room_reservation'

urlpatterns = [
    path('', show, name='show'),
]
