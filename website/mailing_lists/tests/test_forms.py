from unittest.mock import patch

from django.test import TestCase

from mailing_lists.forms import SuffixTextInputWidget


class SuffixWidgetTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass

    def setUp(self):
        pass

    @patch("django.forms.TextInput.__init__")
    def test_suffix_widget_init(self, super_widget_init):
        SuffixTextInputWidget(suffix="testsuffix")
        super_widget_init.assert_called()

    @patch("django.forms.TextInput.render")
    def test_suffix_widget_render(self, render):
        render.return_value = "<a>somehtml</a>"
        test_suffix = "testsuffix"
        widget = SuffixTextInputWidget(suffix="testsuffix")
        self.assertEqual(widget.render(None, None), render.return_value + test_suffix)
