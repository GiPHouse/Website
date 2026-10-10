# Development and Contributing

The website has multiple settings. By default, the development settings (`website/giphousewebsite/settings/development.py`) are used.

- [Getting Started](#getting-started)
  - [Logging into the Backend](#logging-into-the-backend)
- [Dependency Management](#dependency-management)
- [Fixtures](#fixtures)
- [Tests](#tests)
- [Code quality](#code-quality)

## Getting Started
Follow these steps to set up your own development environment. Commands are run from the repository root unless stated otherwise.

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/). uv installs Python 3.14 for you if it is missing.
2. Clone this repository and open a terminal in its root.
3. Run `uv sync`. This creates the virtual environment in `.venv/` and installs all dependencies into it.
4. Run `uv run python website/manage.py migrate` to create the local SQLite database (`website/db.sqlite3`).
5. Run `uv run python website/manage.py runserver` and open [http://localhost:8000](http://localhost:8000).

`uv run` runs a command inside the virtual environment, so you do not have to activate it. If you prefer to activate it, use `source .venv/bin/activate` (Linux/macOS) or `.venv\Scripts\activate` (Windows) and drop the `uv run` prefix.

The database file is ignored by git, so the data in it (including any users you create) stays on your machine.

The site runs without any GitHub credentials, but logging in (including into the admin) does not work until you finish [Logging into the Backend](#logging-into-the-backend).

### Logging into the Backend
Users log in with GitHub only; there are no passwords. To log in locally you need your own GitHub OAuth credentials and a user in your local database with your GitHub ID.

1. **Create a GitHub OAuth App (not a GitHub App).** On GitHub, go to *Settings → Developer settings → **OAuth Apps** → New OAuth App* ([direct link](https://github.com/settings/applications/new)) and fill in:
   - **Application name**: anything, e.g. `GiPHouse local`.
   - **Homepage URL**: `http://localhost:8000`
   - **Authorization callback URL**: `http://localhost:8000/oauth/`
   - **Allow wildcard matching**: tick this. It is required, see below.

   Register the app, then click **Generate a new client secret**. Copy the **Client ID** and the client secret.

   The website sends GitHub a callback URL that is a subpath of this one, such as `http://localhost:8000/oauth/login/?next=/admin/` for logging in and `http://localhost:8000/oauth/register/?next=...` for registering. GitHub only accepts these subpaths when **Allow wildcard matching** is ticked; without it GitHub refuses the redirect and login fails. You can also tick it later in the app's settings.

   > [!IMPORTANT]
   > Make an **OAuth App**, not a **GitHub App**. They are two different things on separate tabs under *Developer settings*, and their forms look alike. Check that the page you are on says *Register a new OAuth application*. A GitHub App is only needed for repository synchronisation ([GitHub App and G Suite setup](integrations.md)), not for logging in.

2. **Set the credentials as environment variables.** The settings read `DJANGO_GITHUB_CLIENT_ID` and `DJANGO_GITHUB_CLIENT_SECRET` (see `website/giphousewebsite/settings/development.py`). The easiest way is a `.env` file in the repository root (it is ignored by git):
   ```
   DJANGO_GITHUB_CLIENT_ID=<your client id>
   DJANGO_GITHUB_CLIENT_SECRET=<your client secret>
   ```
   and pass it to every `uv run` command with `--env-file .env`. Alternatively export them in your shell (`export NAME=value` in bash/zsh, `$env:NAME="value"` in PowerShell) or use [direnv](https://direnv.net/).

3. **Create a superuser for your GitHub account.** Look up your numeric GitHub ID at `https://api.github.com/users/<your_github_username>` (the `id` field), then run:
   ```bash
   uv run python website/manage.py createsuperuser --github_id=<your_github_id> --github_username=<your_github_username> --no-input
   ```

4. **Start the server with the credentials loaded.** The client ID is read when the server starts, so restart it after changing the variables:
   ```bash
   uv run --env-file .env python website/manage.py runserver
   ```

5. **Log in.** Open [http://localhost:8000/admin/](http://localhost:8000/admin/). You are sent to GitHub, asked to authorize your app, and sent back logged in.

Use the same host name in the browser as in the callback URL. GitHub treats `localhost` and `127.0.0.1` as different hosts, so if you browse to `http://127.0.0.1:8000`, register `http://127.0.0.1:8000/oauth/` as the callback URL instead (or add both; an OAuth App accepts several callback URLs).

Logging in only works for GitHub accounts that already exist as a user in your local database. Any other account is sent to the registration page if a semester has open registrations, and otherwise sees "Login Failed".


## Dependency Management
The Python dependencies are managed using a tool called [uv](https://docs.astral.sh/uv/), which automatically creates virtual environments that ease development and makes it easy to manage the dependencies.

## Fixtures
To make testing in your development environment easier, the management command `createfixtures` exists. This management command is supposed to create dummy data in your local database, but it does not work at the moment.
<!---
```Bash
$ python website/manage.py createfixtures
```

Use the `--help` argument to get more information.
--->

## Tests
To make sure everything functions correctly, the website has tests (using [Djangos built-in test framework](https://docs.djangoproject.com/en/dev/topics/testing/)). To run these manually use
```Bash
$ uv run python website/manage.py test website/
```

## Code quality
The code of this project has high standards. This is enforced by continuous integration ([GitHub Actions](https://help.github.com/en/actions/automating-your-workflow-with-github-actions)).

- [PEP 8](https://www.python.org/dev/peps/pep-0008/) (Python styling) is enforced by using `ruff`.
  - Run `ruff format . ` to format the codebase.
- Test coverage (both statement and branch coverage) is enforced by using [Coverage.py](https://coverage.readthedocs.io/en/coverage-5.0.3/).
  - The website has at least 95% test coverage.
- [PEP 257](https://www.python.org/dev/peps/pep-0257/) (Python docstring conventions) is enforced by [`ruff`](https://github.com/PyCQA/pydocstyle).
  - PEP 257 forces every function, method and class to have documentation.
