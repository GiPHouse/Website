from django.test import TestCase
from django.template import Context, Template

from ..links import URL_GITHUB_LOGIN


class GithubTagsTest(TestCase):

    def test_tag(self):
        """
        Test url_github_login tag.
        """

        template_to_render = Template(
            '''{% load github_tags %}<a href="{% url_github_login %}"></a>'''
        )
        rendered_template = template_to_render.render(Context())

        self.assertInHTML(
            f'<a href="{ URL_GITHUB_LOGIN }"></a>',
            rendered_template
        )
