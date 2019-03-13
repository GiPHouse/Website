from django.shortcuts import render
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Reservation, Room
from .forms import ReservationForm
from datetime import timedelta, datetime
from django.utils import timezone
from django.core.exceptions import PermissionDenied


def show_calendar(request):
    reservations = Reservation.objects.all()
    rooms = Room.objects.all()
    today = timezone.now().date()

    if 'week' in request.GET:
        current_week = request.GET['week']
        monday_of_the_week = datetime.strptime(
            f'{today.year}-{current_week}-1-', "%Y-%W-%w").date()

    else:
        current_week = today.isocalendar()[1]
        monday_of_the_week = today - \
            timedelta(days=(today.isocalendar()[2] - 1))

    this_weeks_reservations = []
    for day, n in ((monday_of_the_week + timedelta(days=n), n) for n in range(7)):
        next_day = day + timedelta(days=1)
        this_weeks_reservations += [Reservation.objects.filter(
            start_time__date__gte=day,
            start_time__date__lte=next_day,
        )]

    context = {
        'reservations': reservations,
        'rooms': rooms,
        'this_weeks_reservations': this_weeks_reservations,
        'current_week': current_week,
    }
    return render(request, 'room_reservation/index.html', context)


class CreateReservationView(LoginRequiredMixin, CreateView):
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'
    raise_exception = True

    def form_valid(self, form):
        reservation = form.save(commit=False)
        reservation.reservee = self.request.user
        reservation.save()
        return super().form_valid(form)


class UpdateReservationView(LoginRequiredMixin, UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'
    raise_exception = True

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(UpdateView, self).get_object()
        if not obj.reservee == self.request.user:
            raise PermissionDenied
        return obj


class DeleteReservationView(LoginRequiredMixin, DeleteView):
    model = Reservation
    success_url = '/reservations/'
    raise_exception = True

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(DeleteView, self).get_object()
        if not obj.reservee == self.request.user:
            raise PermissionDenied
        return obj
