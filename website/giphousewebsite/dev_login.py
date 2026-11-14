from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import TemplateView, View

from giphousewebsite.mixins import DebugOnlyMixin


class DevLoginView(DebugOnlyMixin, TemplateView):
    """
    Only allow users to see the "login as any user" page when we are in
    development.
    """

    template_name = "dev_login.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get("q", "")
        if query:
            users = get_user_model().objects.filter(
                Q(github_username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        else:
            users = get_user_model().objects.all()
        context["query"] = query
        context["users"] = users[:25]
        return context


class DevLoginAsView(DebugOnlyMixin, View):
    """
    Only allow users to log in as someone else when we are in development!
    """

    def post(self, request, pk):
        """
        Handle the login request on a post as the given user pk.
        This view is guarded by the DebugOnlyMixin, so it can only occur when
        settings.DEBUG is set to True which *should* only be the case in
        development, but just in case, we'll check that we're running locally
        as well so this definitely cannot be done on the real server.
        """
        # REMOTE_ADDR is the real client address here: in production
        # nginx-proxy runs in a separate container and forwards requests over
        # the uwsgi protocol, which passes the client IP along. This check is
        # only safe as long as that holds; see docs/deployment.md.
        if request.META["REMOTE_ADDR"] in ("127.0.0.1", "::1"):
            user = get_object_or_404(get_user_model(), pk=pk)
            login(request, user)
            return redirect("home")
        messages.error(request, "Dev login only works from localhost.")
        return redirect("dev-login")
