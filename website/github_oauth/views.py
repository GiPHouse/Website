from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, get_user_model
from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponseBadRequest
from django.contrib import messages
from github_oauth.backends import GithubOAuthBackend

User = get_user_model()


@require_http_methods(['GET', ])
def github_login(request):
    """
    View accessed by GitHub after an authorization request of a user trying to login.

    :param request: Object containing information about request user made.
    :return: Redirect to homepage with a login status message.
    """
    if 'code' not in request.GET:
        return HttpResponseBadRequest()

    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in", extra_tags='alert alert-success')
        return redirect('home')

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


@require_http_methods(['GET', ])
def github_register(request):
    """
    View accessed by GitHub after an authorization request of a user trying to register.

    :param request: Object containing information about request user made.
    :return: Redirect to homepage with a login status message.
    """

    if 'code' not in request.GET:
        return HttpResponseBadRequest()

    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in", extra_tags='alert alert-success')
        return redirect('home')

    code = request.GET['code']

    backend = GithubOAuthBackend()
    github_info = backend.get_github_info(code)

    try:
        user = User.objects.get(giphouseprofile__github_id=github_info['id'])
    except User.DoesNotExist:
        pass
    else:
        login(
            request,
            user,
            backend='github_oauth.backends.GithubOAuthBackend',
        )
        return redirect('home')

    session = request.session
    session['github_id'] = github_info['id']
    session['github_username'] = github_info['login']
    session['github_email'] = github_info['email']
    session['github_name'] = github_info['name']

    return redirect('registrations:step2')
