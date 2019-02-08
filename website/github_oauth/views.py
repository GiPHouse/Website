from django.shortcuts import redirect
from django.contrib.auth import authenticate, login
from django.views.decorators.http import require_http_methods

from django.http.response import HttpResponseNotFound

from django.contrib import messages


@require_http_methods(['GET', ])
def github_callback(request):

    if 'code' not in request.GET or request.user.is_authenticated:
        return HttpResponseNotFound()

    code = request.GET['code']

    user = authenticate(request, code=code)

    if user is not None:
        login(request, user)

        messages.success(
            request, 'Login Successful', extra_tags='alert alert-success'
        )

        return redirect('home')

    messages.warning(request, 'Login Failed', extra_tags='alert alert-danger')
    return redirect('home')
