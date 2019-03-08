from django.shortcuts import render
from django.views.generic.edit import FormView, CreateView
from .models import Reservation, Room
from .forms import ReservationForm


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
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'

    def form_valid(self, form):
        form_with_user = form.save(commit=False)
        form_with_user.user = self.request.user
        return super().form_valid(form_with_user)
