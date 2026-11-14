from django.test import TestCase

from tasks.models import Task


class ModelsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.total = 2
        cls.completed = 1
        cls.fail = True
        cls.redirect_url = "redirect"

        cls.test_task = Task.objects.create(
            total=cls.total,
            completed=cls.completed,
            fail=cls.fail,
            redirect_url=cls.redirect_url,
        )

    def test_task_model_str_method(self):
        self.assertEqual(
            f"Task with {self.completed} done out of {self.total} and "
            f"failed with redirect to {self.redirect_url}",
            str(self.test_task),
        )
