from django.urls import path

from .views import show_calendar,CreateReservationView,DeleteReservationView, UpdateReservationView

app_name = 'room_reservation'

urlpatterns = [
    path('', show_calendar, name='calendar'),
    path('create', CreateReservationView.as_view(), name='create_reservation'),
    path('<int:pk>/update', UpdateReservationView.as_view(), name='update_reservation'),
    path('<int:pk>/delete', DeleteReservationView.as_view(), name='delete_reservation'),
    ]
