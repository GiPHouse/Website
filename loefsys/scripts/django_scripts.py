"""Submodule containing scripts related to Django.

With the available functions, several django-admin functions are accessible.
"""

import subprocess


def runserver() -> None:
    """Boot up Django's development webserver.

    See :djadmin:`django:runserver` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "runserver"], check=False
    )


def makemigrations() -> None:
    """Make migrations based on the changes in the code.

    See :djadmin:`django:makemigrations` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "makemigrations"],
        check=False,
    )


def migrate() -> None:
    """Apply migrations to the database.

    See :djadmin:`django:migrate` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "migrate"], check=False
    )


def test() -> None:
    """Run tests for all installed apps.

    See :djadmin:`django:test` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "test"], check=False
    )


def createsuperuser() -> None:
    """Create an admin user for the database.

    See :djadmin:`django:createsuperuser` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "createsuperuser"],
        check=False,
    )


def collectstatic() -> None:
    """Collect all static files in the ``static`` folder.

    See :djadmin:`django:collectstatic` for more details.
    """
    subprocess.run(
        ["poetry", "run", "python", "-m", "loefsys.manage", "collectstatic"],
        check=False,
    )
