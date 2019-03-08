from django.shortcuts import render
from django.views.generic.edit import FormView, CreateView, DeleteView, UpdateView
from .models import Reservation, Room
from .forms import ReservationForm
from datetime import timedelta,datetime
from django.utils import timezone
from django.http import Http404
import pytz

# https://stackoverflow.com/questions/51194745/get-first-and-last-day-of-given-week-number-in-python
def get_start_and_end_date_from_calendar_week(year, calendar_week):       
    monday = datetime.strptime(f'{year}-{calendar_week}-1', "%Y-%W-%w").date()
    return monday, monday + timedelta(days=6.9)

def show(request):
    reservations = Reservation.objects.all()
    rooms = Room.objects.all()
    today = timezone.now().date()
    if 'week' in request.GET:
        print('jeeej')
        current_week = request.GET['week']
        monday_of_the_week, _ = get_start_and_end_date_from_calendar_week(today.year,current_week)
    else:
        current_week = today.isocalendar()[1]
        monday_of_the_week = today - timedelta(days=(today.isocalendar()[2] - 1))
	
    this_weeks_reservations = []
    for day, n in ( (monday_of_the_week + timedelta(days=n), n) for n in range(7)):
        next_day = day + timedelta(days=1)
        this_weeks_reservations += [Reservation.objects.filter(
            start_time__gte=day,
            start_time__lte=next_day,
        )]
    

    context = {
        'reservations': reservations,
        'rooms': rooms,
        'this_weeks_reservations' : this_weeks_reservations,
        'current_week': current_week,
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
        reservation = form.save(commit=False)
        reservation.reservee = self.request.user
        reservation.save()
        return super().form_valid(form)

class UpdateReservationView(UpdateView):
    model = Reservation
    form_class = ReservationForm
    template_name = 'room_reservation/reservation_form.html'
    success_url = '/reservations/'

class DeleteReservationView(DeleteView):
    model = Reservation
    success_url = '/reservations/'

    def get_object(self, queryset=None):
        """ Hook to ensure object is owned by request.user. """
        obj = super(DeleteView, self).get_object()
        if not obj.reservee == self.request.user:
            raise Http404
        return obj
