from urllib.parse import quote

from django import template
from django.shortcuts import reverse

from github_oauth.links import URL_GITHUB_LOGIN


register = template.Library()


@register.simple_tag(takes_context=True)
def url_github_callback(context, callback_action):
    """
    Tag used to load GitHub login/authorization url into templates.

    :param context: context of the request that requested the template.
    :param callback_action: An url name from github_oauth to redirect to after successful authentication.
        A new url is created based on the callback_action and the current path.
        The current path is added as the 'next' parameter to the redirect_uri.
        The Github OAuth callback view can use the 'next' parameter to redirect the user to the same page.
    :return: url to request GitHub OAuth authentication with an optional redirect.
    """
    request = context["request"]
    callback = request.build_absolute_uri(reverse(f"github_oauth:{callback_action}"))
    callback = f"{callback}?next={request.path}"
    return f"{URL_GITHUB_LOGIN}&redirect_uri={quote(callback)}"
