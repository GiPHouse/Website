from django.urls import path

from room_reservation.views import ShowCalendarView
from room_reservation.views import CreateReservationView
from room_reservation.views import DeleteReservationView
from room_reservation.views import UpdateReservationView

app_name = 'room_reservation'

urlpatterns = [
    path('', ShowCalendarView.as_view(), name='calendar'),
    path('create', CreateReservationView.as_view(), name='create_reservation'),
    path('<int:pk>/update', UpdateReservationView.as_view(),
         name='update_reservation'),
    path('<int:pk>/delete', DeleteReservationView.as_view(),
         name='delete_reservation'),
]
