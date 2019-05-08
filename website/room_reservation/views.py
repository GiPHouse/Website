from datetime import datetime, timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from room_reservation.forms import ReservationForm
from room_reservation.models import Reservation, Room


class ShowCalendarView(LoginRequiredMixin, TemplateView):
    """
    Show a week-calendar and showing the current reservations.

    From here, it is possible to make reservations,
    and to update and delete your own.
    """

    template_name = 'room_reservation/index.html'

    def get_context_data(self, **kwargs):
        """Load all information for the calendar."""
        context = super(ShowCalendarView, self).get_context_data(**kwargs)

        rooms = Room.objects.all()
        this_weeks_reservations = {}
        today = timezone.now().date()

        if 'week' in self.request.GET:
            current_week = self.request.GET['week']
        else:
            current_week = today.isocalendar()[1]

        monday_of_the_week = datetime.strptime(
            f'{today.year}-{current_week}-1', "%G-%V-%w").date()
        days = [monday_of_the_week + timedelta(days=n) for n in range(7)]

        for room in rooms:
            room.reservations = []
            for day in days:
                next_day = day + timedelta(days=1)
                room.reservations += [Reservation.objects.filter(
                    room=room,
                    start_time__date__gte=day,
                    start_time__date__lt=next_day,
                )]

        context['rooms'] = rooms
        context['current_week'] = current_week
        context['days'] = days

        return context


class CreateReservationView(LoginRequiredMixin, CreateView):
    """FormView to make a reservation."""

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
    """FormView to update your reservation."""

    model = Reservation
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'
    raise_exception = True

    def get_object(self, queryset=None):
        """Ensure object is owned by request.user."""
        obj = super(UpdateView, self).get_object()
        if not obj.reservee == self.request.user:
            raise PermissionDenied
        return obj


class DeleteReservationView(LoginRequiredMixin, DeleteView):
    """FormView to delete your reservation."""

    model = Reservation
    success_url = '/reservations/'
    raise_exception = True

    def get_object(self, queryset=None):
        """Ensure object is owned by request.user."""
        obj = super(DeleteView, self).get_object()
        if not obj.reservee == self.request.user:
            raise PermissionDenied
        return obj
