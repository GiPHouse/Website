from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin


class LoginRequiredMessageMixin(LoginRequiredMixin):
    """LoginRequiredMixin that sets a message for unauthenticated users."""

    message = "You need to be logged in to view that page."

    def handle_no_permission(self):
        """Set message and handle unauthenticated user."""
        messages.warning(self.request, self.message, extra_tags="warning")
        return super().handle_no_permission()
