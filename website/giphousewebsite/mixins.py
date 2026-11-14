from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404


class LoginRequiredMessageMixin(LoginRequiredMixin):
    """LoginRequiredMixin that sets a message for unauthenticated users."""

    message = "You need to be logged in to view that page."

    def handle_no_permission(self):
        """Set message and handle unauthenticated user."""
        messages.warning(self.request, self.message, extra_tags="warning")
        return super().handle_no_permission()


class DebugOnlyMixin:
    """
    A mixin that denies the existence of a page that should only be available
    during development.
    """

    def dispatch(self, request, *args, **kwargs):
        """If we're in production, act like this page does not exist."""
        if not settings.DEBUG:
            raise Http404
        return super().dispatch(request, *args, **kwargs)
