from django.urls import path

from .views import show,CreateReservationView

app_name = 'room_reservation'

urlpatterns = [
    path('', show, name='show'),
    path('create', CreateReservationView.as_view(), name='create_reservation'),
]
