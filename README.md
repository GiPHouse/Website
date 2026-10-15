<div align="center">

<a href="https://giphouse.nl/">
<img src="website/giphousewebsite/static/img/favicon/android-chrome-512x512.png" height=150>
</a>

# __GiPHouse website__

[![License](https://img.shields.io/badge/License-AGPL--3.0-742e68?style=flat)](https://www.gnu.org/licenses/agpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.14-ffdd54?logo=python&logoColor=ffdd54&labelColor=3776AB)](https://docs.python.org/3.14/)
[![Ruff](https://img.shields.io/badge/Ruff-0.15-D7FF64?logo=Ruff&logoColor=D7FF64&labelColor=261230)](https://docs.astral.sh/ruff/)
[![uv](https://img.shields.io/badge/uv-0.11-DE5FE9?logo=uv&logoColor=DE5FE9&labelColor=261230)](https://docs.astral.sh/uv/)
[![Code style: Black](https://img.shields.io/badge/Code%20style-Black-000000.svg)](https://black.readthedocs.io/en/stable/the_black_code_style/current_style.html)\
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-e5e1ea?logo=bootstrap&logoColor=e5e1ea&labelColor=7952B3)](https://getbootstrap.com/docs/5.3)
[![Font_Awesome](https://img.shields.io/badge/Font_Awesome-5.13-f0f1f3?logo=fontawesome&logoColor=f0f1f3&labelColor=538DD7)](https://docs-v5.fontawesome.com/)
[![Django](https://img.shields.io/badge/Django-6.0-44B78B?logo=django&logoColor=white&labelColor=092E20)](https://docs.djangoproject.com/en/6.0/)\
[![Linting](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/linting.yml/badge.svg)](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/linting.yml)
[![Testing](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/testing.yml/badge.svg)](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/testing.yml)
[![Coverage](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/coverage.yml/badge.svg)](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/coverage.yml)
[![Deployment](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/deployment.yml/badge.svg)](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/deployment.yml)
[![Dependabot Updates](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/GiPHouse/GiPHouse-Website/actions/workflows/dependabot/dependabot-updates)

This is the code for the website of [GiPHouse](https://giphouse.nl/) powered by [Django](https://www.djangoproject.com/).
</div>

## Quick start

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) installed. From the repository root:

```bash
uv sync
uv run python website/manage.py migrate
uv run python website/manage.py runserver
```

Then open [http://localhost:8000](http://localhost:8000). To log in (including into `/admin/`), you need a GitHub **OAuth App** (not a GitHub App) with **Allow wildcard matching** ticked, and a local superuser; follow [Logging into the Backend](docs/development.md#logging-into-the-backend).

## Documentation

| Document | What it covers |
| --- | --- |
| [Features](docs/features.md) | Authentication, semesters, registrations and automatic teams, questionnaires, room reservations, GitHub and mailing list synchronisation, tasks |
| [Development](docs/development.md) | Local setup, GitHub OAuth login, dependencies, fixtures, tests and code quality |
| [GitHub App and G Suite setup](docs/integrations.md) | Registering the GitHub App for repository sync and the G Suite service account for mailing lists |
| [Deployment](docs/deployment.md) | Docker image and Compose services, the deployment pipeline, secrets and server setup |

## License

This project is licensed under the [AGPL-3.0](COPYING).
