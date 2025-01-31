"""Submodule containing scripts related to the repository code.

With the available scripts, linting, formatting, and typechecking is easily available.
"""

import subprocess


def lint() -> None:
    """Apply linting to the project code.

    See `Ruff linter <https://docs.astral.sh/ruff/linter/>`_ for more details.
    """
    subprocess.run(["ruff", "check"], check=False)


def format() -> None:  # noqa: A001
    """Apply formatting to the project code.

    See `Ruff formatter <https://docs.astral.sh/ruff/formatter/>`_ for more details.
    """
    subprocess.run(["ruff", "format"], check=False)


def typecheck() -> None:
    """Perform typechecking analysis on the project code.

    See :doc:`mypy <mypy:index>` for more details
    """
    subprocess.run(["mypy", "-p", "loefsys"], check=False)
