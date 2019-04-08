from unittest import mock

from django.test import TestCase
from django.template import Context, Template
from django.shortcuts import reverse

from github_oauth.links import URL_GITHUB_LOGIN


class GithubTagsTest(TestCase):

    def test_tag_no_action(self):
        """
        Test url_github_login tag.
        """

        template_to_render = Template(
            '''{% load github_tags %}<a href="{% url_github_callback %}"></a>'''
        )
        rendered_template = template_to_render.render(Context())

        self.assertInHTML(
            f'<a href="{ URL_GITHUB_LOGIN }"></a>',
            rendered_template
        )

    def test_tag_action(self):
        """
        Test url_github_login tag with a callback action.
        """

        callback_action = 'login'
        callback_url = reverse(f'github_oauth:{ callback_action }')
        fake_domain = f'http://fake_domain{ callback_url }'

        template_to_render = Template(
            f'''{{% load github_tags %}}<a href="{{% url_github_callback '{ callback_action }' %}}"></a>'''
        )

        context = Context()
        context['request'] = mock.MagicMock()
        context['request'].build_absolute_uri = mock.MagicMock(
            return_value=fake_domain
        )

        rendered_template = template_to_render.render(context)

        self.assertInHTML(
            f'<a href="{ URL_GITHUB_LOGIN  }&redirect_uri={ fake_domain }"></a>',
            rendered_template
        )
