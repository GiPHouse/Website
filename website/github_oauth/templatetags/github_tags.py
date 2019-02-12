from django import template

from ..links import URL_GITHUB_LOGIN

register = template.Library()


@register.simple_tag
def url_github_login():
    """
    Tag used to load GitHub login/authorization url into templates.
    :return: GitHub login/authorization url
    """
    return URL_GITHUB_LOGIN
