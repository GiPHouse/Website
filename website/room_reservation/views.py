from django.shortcuts import render
from django.views.generic.edit import CreateView, DeleteView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Reservation, Room
from .forms import ReservationForm
from datetime import timedelta, datetime
from django.utils import timezone
from django.core.exceptions import PermissionDenied


def show_calendar(request):
    """
    Show a week-calendar and showing the current reservations.
    From here, it is possible to make reservations,
    and to update and delete your own.
    """
    rooms = Room.objects.all()
    this_weeks_reservations = []
    today = timezone.now().date()

    if 'week' in request.GET:
        current_week = request.GET['week']
    else:
        current_week = today.isocalendar()[1]

    monday_of_the_week = datetime.strptime(
        f'{today.year}-{current_week}-1', "%G-%V-%w").date()
    days = (monday_of_the_week + timedelta(days=n) for n in range(7))

    for day in days:
        next_day = day + timedelta(days=1)
        this_weeks_reservations += [Reservation.objects.filter(
            start_time__date__gte=day,
            start_time__date__lt=next_day,
        )]

    context = {
        'rooms': rooms,
        'this_weeks_reservations': this_weeks_reservations,
        'current_week': current_week,
    }
    return render(request, 'room_reservation/index.html', context)


class CreateReservationView(LoginRequiredMixin, CreateView):
    """
    FormView to make a reservation
    """
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'
    raise_exception = True

    def form_valid(self, form):
        """
        Save the form as model.
        Auto-fill the logged in user as reservee.
        """
        reservation = form.save(commit=False)
        reservation.reservee = self.request.user
        reservation.save()
        return super().form_valid(form)


class UpdateReservationView(LoginRequiredMixin, UpdateView):
    """
    FormView to update your reservation.
    """
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
    """
    FormView to delete your reservation.
    """
    model = Reservation
    success_url = '/reservations/'
    raise_exception = True

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(DeleteView, self).get_object()
        if not obj.reservee == self.request.user:
            raise PermissionDenied
        return obj
