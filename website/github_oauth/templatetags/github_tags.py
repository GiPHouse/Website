from django import template
from django.shortcuts import reverse

from ..links import URL_GITHUB_LOGIN

register = template.Library()


@register.simple_tag(takes_context=True)
def url_github_callback(context, redirect_uri='login'):
    """
    Tag used to load GitHub login/authorization url into templates.
    :return: GitHub login/authorization url
    """
    request = context['request']
    callback = request.build_absolute_uri(reverse('github_oauth:oauth'))
    return URL_GITHUB_LOGIN + f'&redirect_uri={callback}{redirect_uri}'
