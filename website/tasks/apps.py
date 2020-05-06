from django.apps import AppConfig


class TasksConfig(AppConfig):
    """
    App config for Tasks.

    A task is a process that takes more time that can fit in a request.
    The process is run in a separate thread and the status is synced to the task.
    The task is then used to show the user the progress and redirect them when it is finished.
    """

    name = "tasks"
