from django.urls import path

from .views import show,CreateReservationView,DeleteReservationView, UpdateReservationView

app_name = 'room_reservation'

urlpatterns = [
    path('', show, name='show'),
    path('create', CreateReservationView.as_view(), name='create_reservation'),
    path('update/<int:pk>/', UpdateReservationView.as_view(), name='update_reservation'),
    path('delete/<int:pk>/', DeleteReservationView.as_view(), name='delete_reservation'),
    ]
