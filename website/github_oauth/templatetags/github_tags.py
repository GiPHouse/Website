from django import template

from ..links import URL_GITHUB_LOGIN

register = template.Library()


@register.simple_tag
def url_github_login():
    return URL_GITHUB_LOGIN
