"""Submodule containing scripts related to Sphinx docs generation.

The available scripts allow generation of the API docs and building of the docs.
"""

import subprocess


def makedocs() -> None:
    """Generate HTML documentation for the project.

    See :doc:`sphinx:man/sphinx-build` for more details.
    """
    subprocess.run(
        ["sphinx-build", "-M", "html", "./docs", "./docs/_build", "-E"], check=False
    )


def genapidocs() -> None:
    """Generate API documentation from the docstrings.

    See :doc:`sphinx:man/sphinx-apidoc` for more details.
    """
    subprocess.run(
        [
            "sphinx-apidoc",
            "-M",
            "-f",
            "-e",
            "--remove-old",
            "-o",
            "./docs/api",
            "./loefsys",
            "./loefsys/*/migrations",
            "./loefsys/manage.py",
            "./loefsys/*/tests*",
        ],
        env={"SPHINX_APIDOC_OPTIONS": "members,show-inheritance"},
        check=False,
    )
