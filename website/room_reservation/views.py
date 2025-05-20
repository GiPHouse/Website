import json
from json import JSONDecodeError

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponseBadRequest, JsonResponse
from django.utils import dateparse, timezone
from django.views import View
from django.views.generic import TemplateView

from courses.models import Semester

from room_reservation.models import Reservation, Room, in_special_availability


class BaseReservationView(View):
    """Base class for reservation API endpoints."""

    time_window_future = timezone.timedelta(days=14)
    time_window_past = timezone.timedelta(days=30)

    def validate(self, user, room, start_time, end_time, pk=None):
        """
        Validate the input for the reservation.

        By checking:

        - All checks made by ModelForm.
        - Reservation does not collide with another reservation.
        - Reservation is not too long.
        """
        start_time = start_time.astimezone(timezone.get_current_timezone())
        end_time = end_time.astimezone(timezone.get_current_timezone())

        if start_time.date() < timezone.now().date():
            return False, "Reservation cannot be made in the past."

        if start_time.date() > timezone.now().date() + self.time_window_future:
            return False, "Reservation too far in the future."

        if end_time.date() - start_time.date() >= timezone.timedelta(days=1):
            return False, "Reservation too long. Please shorten your reservation"

        if start_time >= end_time:
            return False, "Start time needs to be before end time"

        if start_time.hour < 8 or start_time.hour >= 18 or end_time.hour < 8 or end_time.hour > 18:
            return False, "Please enter times between 8:00 and 18:00"

        if start_time.weekday() in (5, 6):
            return False, "Rooms cannot be reserved in the weekends"

        room = Room.objects.get(id=room)
        if (
            room.special_availability is not None
            and room.special_availability != []
            and not in_special_availability(room.special_availability, start_time, end_time)
        ):
            return False, "Rooms is not available at this time"

        already_taken = (
            Reservation.objects.filter(room=room)
            .filter(
                Q(start_time__lte=start_time, end_time__gt=start_time)
                | Q(start_time__lt=end_time, end_time__gte=end_time)
                | Q(start_time__gte=start_time, end_time__lte=end_time)
            )
            .exclude(pk=pk)
            .exists()
        )

        if already_taken:
            return False, "Room already reserved in this timeslot"
        return True, None

    def load_json(self):
        """Extract the json data from text_body."""
        body = json.loads(self.request.body)
        room = body["room"]
        start_time = dateparse.parse_datetime(body["start_time"])
        end_time = dateparse.parse_datetime(body["end_time"])
        return room, start_time, end_time

    def can_edit(self, reservation):
        """Return true if the reservation can be edited by the logged in user."""
        return (
            self.request.user == reservation.reservee
            or self.request.user.is_superuser
        )
    
    def can_create(self):
        """Return true if the reservation can be created by the logged in user."""
        current_semester = Semester.objects.get_or_create_current_semester()

        return (
            self.request.user.registration_set.filter(projects_set__semester=current_semester).exists()
            or self.request.user.is_superuser
        )


class ShowCalendarView(TemplateView, BaseReservationView):
    """
    Show a week-calendar and showing the current reservations.

    From here, it is possible to make reservations,
    and to update and delete your own.
    """

    template_name = "room_reservation/index.html"

    def _reservation_title(self, reservation):
        """Return the title of the reservation."""
        room_name = reservation.room.name
        reservee_registrations = reservation.reservee.registration_set.filter(
            semester=Semester.objects.get_or_create_current_semester()
        )
        team_name = reservee_registrations.first().project if reservee_registrations.exists() else None
        reservee_display_name = reservation.reservee.first_name if reservation.reservee != self.request.user else "you"
        return f"{room_name} {team_name}" if team_name else f"{room_name} ({reservee_display_name})"

    def get_context_data(self, **kwargs):
        """Load all information for the calendar."""
        context = super(ShowCalendarView, self).get_context_data(**kwargs)

        context["reservations"] = json.dumps(
            [
                {
                    "pk": reservation.pk,
                    "title": self._reservation_title(reservation),
                    "reservee": reservation.reservee.get_full_name(),
                    "room": reservation.room_id,
                    "start": reservation.start_time.isoformat(),
                    "end": reservation.end_time.isoformat(),
                    "editable": self.can_edit(reservation),
                }
                for reservation in Reservation.objects.filter(
                    start_time__date__gte=timezone.now() - self.time_window_past,
                    start_time__date__lte=timezone.now() + self.time_window_future,
                )
            ]
        )
        context["rooms"] = Room.objects.all()
        return context


class CreateReservationView(LoginRequiredMixin, BaseReservationView):
    """View to make a reservation."""

    raise_exception = True

    def post(self, request, *args, **kwargs):
        """Handle the POST method for this view."""
        try:
            room, start_time, end_time = self.load_json()
        except (KeyError, JSONDecodeError):
            return HttpResponseBadRequest(json.dumps({"ok": "False", "message": "Bad request"}))
        
        if not self.can_create():
            return JsonResponse({"ok": False, "message": "You are not allowed to make reservations."})

        ok, message = self.validate(room, start_time, end_time)
        if not ok:
            return JsonResponse({"ok": False, "message": message})

        reservation = Reservation.objects.create(
            reservee=request.user, room_id=room, start_time=start_time, end_time=end_time
        )
        return JsonResponse({"ok": True, "pk": reservation.pk})


class UpdateReservationView(LoginRequiredMixin, BaseReservationView):
    """View to update your reservation."""

    raise_exception = True

    def post(self, request, pk, *args, **kwargs):
        """Handle the POST method for this view."""
        try:
            room, start_time, end_time = self.load_json()
        except (KeyError, JSONDecodeError):
            return HttpResponseBadRequest(json.dumps({"ok": "False", "message": "Bad request"}))

        try:
            reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return JsonResponse({"ok": False, "message": "This reservation does not exist"})

        if not self.can_edit(reservation):
            return JsonResponse({"ok": False, "message": "You can only update your own events"})

        ok, message = self.validate(room, start_time, end_time, pk=pk)
        if not ok:
            return JsonResponse({"ok": False, "message": message})

        reservation.start_time = start_time
        reservation.end_time = end_time
        reservation.save()
        return JsonResponse({"ok": True})


class DeleteReservationView(LoginRequiredMixin, BaseReservationView):
    """View to delete your reservation."""

    raise_exception = True

    def post(self, request, pk, *args, **kwargs):
        """Handle the POST method for this view."""
        try:
            reservation = Reservation.objects.get(pk=pk)
        except Reservation.DoesNotExist:
            return JsonResponse({"ok": False, "message": "This reservation does not exist"})

        if not self.can_edit(reservation):
            return JsonResponse({"ok": False, "message": "You can only delete your own events"})

        reservation.delete()
        return JsonResponse({"ok": True})
