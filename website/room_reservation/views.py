from django.shortcuts import render
from django.views.generic.edit import FormView, CreateView
from .models import Reservation, Room


def show(request):
    reservations = Reservation.objects.all()
    rooms = Room.objects.all()
    context = {
        'reservations': reservations,
        'rooms': rooms,
    }
    return render(request, 'room_reservation/index.html', context)


class ReservationView(FormView):
    template_name = 'room_reservation/reservation.html'
    success_url = '/reservations/'

    def form_valid(self, form):
        return super().form_valid(form)


class CreateReservationView(CreateView):
    model = Reservation
    success_url = '/reservations/'
    fields = ('reservee', 'room', 'start_time', 'end_time')
