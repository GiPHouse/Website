from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.views import View

from courses.models import Lecture

from lecture_registrations.models import LectureRegistration


class LectureRegistrationView(LoginRequiredMixin, View):
    """Register for a lecture."""

    def post(self, request, pk, *args, **kwargs):
        """Register a user on POST."""
        try:
            lecture = Lecture.objects.get(pk=pk)
        except Lecture.DoesNotExist:
            raise Http404()

        if not lecture.registration_required:
            messages.error(
                request,
                "No registration required for this lecture.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )

        if timezone.now() > lecture.register_until:
            messages.error(
                request,
                "Registration is closed.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )

        user = request.user

        if not user.registration_set.filter(semester=lecture.semester).exists():
            messages.error(
                request,
                "You are not registered for this semester.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )

        if lecture.capacity_reached:
            messages.error(
                request,
                f"Capacity for {lecture} has been reached.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )

        registration, created = LectureRegistration.objects.get_or_create(employee=user, lecture=lecture)
        if created:
            messages.success(
                request,
                f"You are now registered for {lecture}.",
            )
        else:
            messages.info(
                request,
                f"You were already registered for {lecture}.",
            )

        return redirect(
            reverse("courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()])
        )


class LectureUnregistrationView(LoginRequiredMixin, View):
    """Unregister for a lecture."""

    def post(self, request, pk, *args, **kwargs):
        """Unregister a user on POST."""
        try:
            lecture = Lecture.objects.get(pk=pk)
        except Lecture.DoesNotExist:
            raise Http404()

        if timezone.now() > lecture.register_until:
            messages.error(
                request,
                "Registration is closed.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )

        user = request.user

        try:
            registration = LectureRegistration.objects.get(employee=user, lecture=lecture)
        except LectureRegistration.DoesNotExist:
            messages.error(
                request,
                "You were not registered.",
            )
            return redirect(
                reverse(
                    "courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()]
                )
            )
        else:
            registration.delete()

        messages.info(
            request,
            f"You are unregistered for {lecture}.",
        )

        return redirect(
            reverse("courses:lectures", args=[lecture.semester.year, lecture.semester.get_season_display().lower()])
        )
