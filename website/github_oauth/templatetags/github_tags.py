from django import template
from django.shortcuts import reverse

from ..links import URL_GITHUB_LOGIN

register = template.Library()


@register.simple_tag(takes_context=True)
def url_github_callback(context, callback_action=''):
    """
<<<<<<< HEAD
    Tag used to load GitHub login/authorization url into templates.

=======
    Tag used to load GitHub login/authorization url into templates
>>>>>>> Added project pages and dynamically add to the header.
    :param context: context of the request that requested the template.
    :param callback_action: An optional url name from github_oauth
           to redirect to after successful authentication.
    :return: url to request GitHub OAuth authentication
             with an optional redirect.
    """
<<<<<<< HEAD
=======

>>>>>>> Added project pages and dynamically add to the header.
    if callback_action:
        request = context['request']
        callback = request.build_absolute_uri(
            reverse(f'github_oauth:{callback_action}')
        )
        return f'{URL_GITHUB_LOGIN}&redirect_uri={callback}'

    return URL_GITHUB_LOGIN
