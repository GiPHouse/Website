from django.shortcuts import render
from .models import Reservation, Room


def show(request):
    reservations = Reservation.objects.all()
    rooms = Room.objects.all()
    context = {
        'reservations': reservations,
        'rooms': rooms,
    }
    return render(request, 'room_reservation/index.html', context)
