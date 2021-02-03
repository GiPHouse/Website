from unittest.mock import patch

from django.contrib.admin import AdminSite
from django.http import Http404
from django.test import RequestFactory, TestCase
from django.urls import reverse

from tasks.admin import TaskAdmin
from tasks.models import Task


class MyTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.task = Task.objects.create(total=5, completed=0, success_message="test message", redirect_url="test_url")
        cls.task_data = Task.objects.create(
            total=1, completed=0, success_message="test message", redirect_url="test_url", data="data"
        )

    def setUp(self):
        site = AdminSite
        self.task_admin = TaskAdmin(Task, site)
        request_factory = RequestFactory()
        self.request = request_factory.get(reverse("admin:tasks_task_changelist"))

    def test_task_progress(self):
        with self.assertRaises(Http404):
            self.task_admin.task_progress(self.request, 1337)

        response = self.task_admin.task_progress(self.request, self.task.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), {"completed": 0, "total": 5, "hasData": False})

    def test_task_progress_data(self):
        response = self.task_admin.task_progress(self.request, self.task_data.id)
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(str(response.content, encoding="utf8"), {"completed": 0, "total": 1, "hasData": True})

    def test_task_download_no_data(self):
        with self.assertRaises(Http404):
            self.task_admin.task_download(self.request, self.task.id)

    def test_task_download(self):
        response = self.task_admin.task_download(self.request, self.task_data.id)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"data")

    @patch("tasks.admin.render")
    def test_task_progress_bar(self, render):
        self.task_admin.task_progress_bar("request", 0)
        render.assert_called_with("request", "admin/tasks/progress_bar.html", {"task": 0, "title": "Progress"})

    @patch("tasks.admin.messages.error")
    @patch("tasks.admin.messages.success")
    @patch("tasks.admin.redirect")
    def test_task_result(self, redirect, success_message, error_message):
        self.task_admin.task_result(self.request, self.task.id)
        redirect.asser_called_once_with(self.task.redirect_url)

        redirect.reset_mock()
        success_message.reset_mock()
        error_message.reset_mock()

        self.task.fail = True
        self.task.save()
        self.task_admin.task_result(self.request, self.task.id)
        redirect.asser_called_once_with(self.task.redirect_url)
        error_message.assert_called_once()
