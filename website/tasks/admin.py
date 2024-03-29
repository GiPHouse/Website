from django.contrib import admin, messages
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import path

from tasks.models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """A non editable admin for tasks."""

    def has_add_permission(self, request):
        """Tasks should only be added through the other admins."""
        return False

    def has_change_permission(self, request, obj=None):
        """Tasks should only be changed through the other admins."""
        return False

    def task_progress(self, request, task):
        """Show progress of a Task."""
        task = get_object_or_404(Task, pk=task)
        return JsonResponse(
            {
                "completed": task.completed,
                "total": task.total,
                "hasData": (not task.fail and task.data is not None and task.data != ""),
            }
        )

    def task_download(self, request, task):
        """Download the data of a task."""
        t = get_object_or_404(Task, pk=task)
        if t.fail or t.data == "" or t.data is None:
            raise Http404
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="proposed-groups.csv"'
        response.write(t.data)
        return response

    def task_result(self, request, task):
        """Show result of a Task."""
        task = get_object_or_404(Task, pk=task)
        if task.fail:
            messages.error(
                request,
                "Something went wrong while processing the task. Look at the log files for more details.",
            )
        else:
            messages.success(request, task.success_message)
        task.delete()
        return redirect(task.redirect_url)

    def task_progress_bar(self, request, task):
        """Show a progress bar for a Task."""
        return render(request, "admin/tasks/progress_bar.html", {"task": task, "title": "Progress"})

    def get_urls(self):
        """Get admin urls."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "task/<int:task>/",
                self.admin_site.admin_view(self.task_progress_bar),
                name="progress_bar",
            ),
            path(
                "task/<int:task>/progress",
                self.admin_site.admin_view(self.task_progress),
                name="progress",
            ),
            path(
                "task/<int:task>/result",
                self.admin_site.admin_view(self.task_result),
                name="result",
            ),
            path(
                "task/<int:task>/download",
                self.admin_site.admin_view(self.task_download),
                name="download",
            ),
        ]
        return custom_urls + urls
