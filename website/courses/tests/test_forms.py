from courses.forms import year_choices

from django.test import TestCase

from freezegun import freeze_time


class FormCoursesTest(TestCase):

    @freeze_time("2010-01-01")
    def test_year_choices(self):
        """Test year_choices."""

        self.assertEqual(
            year_choices(),
            [(2008, 2008), (2009, 2009), (2010, 2010), (2011, 2011)]
        )
