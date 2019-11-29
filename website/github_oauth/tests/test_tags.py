from unittest import mock
from urllib.parse import quote

from django.shortcuts import reverse
from django.template import Context, Template
from django.test import TestCase

from github_oauth.links import URL_GITHUB_LOGIN


class GithubTagsTest(TestCase):
    def test_tag_action(self):

        callback_action = "login"
        callback_url = reverse(f"github_oauth:{ callback_action }")
        redirect_path = "/path"
        fake_domain = f"http://fake_domain{ callback_url }"
        redirect_uri = quote(f"{fake_domain}?next={redirect_path}")

        template_to_render = Template(
            f"""{{% load github_tags %}}<a href="{{% url_github_callback '{ callback_action }' %}}"></a>"""
        )

        context = Context()
        context["request"] = mock.MagicMock()
        context["request"].build_absolute_uri = mock.MagicMock(return_value=fake_domain)
        context["request"].path = redirect_path

        rendered_template = template_to_render.render(context)

        self.assertInHTML(f'<a href="{ URL_GITHUB_LOGIN  }&redirect_uri={ redirect_uri }"></a>', rendered_template)
