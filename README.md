# GiPHouse website

![](https://github.com/giphouse/Website/workflows/Linting%20and%20Testing/badge.svg) ![](https://github.com/giphouse/Website/workflows/Deploy%20to%20production/badge.svg) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) ![](https://img.shields.io/badge/coverage-100%25-brightgreen)

This is the code for the website of [GiPHouse](http://giphouse.nl/) powered by [Django](https://www.djangoproject.com/).

### Getting Started

1. Install Python 3.8+ and [poetry](https://poetry.eustace.io/) (a Python dependency manager).
2. Clone this repository.
3. Run `poetry install` to install all dependencies into virtual environment.
4. Run `poetry shell` to enter the virtual environment.
5. Run `python website/manage.py migrate` to initialise the database.
5. Run `python website/manage.py createsuperuser` to create an admin account.
6. Run `python website/manage.py runserver` to start the local testing server.

# Testing, Linting and Continuous Integration

To test our code we use multiple testing methods. All of these tests are automatically run by Github Actions when a new pull request is made.
All of these tests need to pass, before a pull request is allowed to be merged into the `master` branch.

If you want to run the tests locally, please look up the relevant test command in the [CI workflow](/.github/workflows/ci.yaml) file.

### Tests

The test suite can be run with the `manage.py` command. The following command can be executed to quickly run all the tests:

```bash
poetry run website/manage.py test website/
```
Every Django app has its own tests (located in the `tests` directory inside the app root). We enforce 100% statement and 100% branch coverage in our tests, to make sure that every line of code and branch is run at least once during testing. We use [`coverage`](https://coverage.readthedocs.io/en/v4.5.x/) to run and analyse these tests.

#### Built-in Django tests
The CI runs built-in Django tests. These tests include checking if there are any database migrations needed but not created yet and checking for common problems.

#### Linting
We use multiple to perform static analyis on our code. The most important one is [`flake8`](http://flake8.pycqa.org/en/latest/), a Python linter that checks whether code is formatted according to [PEP8](https://www.python.org/dev/peps/pep-0008/). In addition we also use the [flake8-import-order](https://github.com/PyCQA/flake8-import-order) to make sure the imports are neatly ordered. We enforce the code style of [Black](https://github.com/psf/black).

We also use [`pydocstyle`](https://github.com/PyCQA/pydocstyle) to enforce that every method, function and class is documented and that documentation is formatted according to [PEP 257](https://www.python.org/dev/peps/pep-0257/).

We also use a few Bash scripts (e.g. for deployment). These are checked using [`shellcheck`](https://github.com/koalaman/shellcheck).

#### Loading Fixtures

To make manual testing easier, we have the `createfixtures` command to automatically create test data. We also test if that command works correctly.

You can  create and load fixtures with the `manage.py createfixtures` command. The fixtures dynamically generated using the [faker](https://pypi.org/project/Faker/) package.

Then you can load the courses testdata fixture with this command:
```bash
python website/manage.py createfixtures
```

See
```bash
python website/manage.py createfixtures --help
```
for more information.

# Serverconfig

The GiPHouse website runs on an AWS EC2 instance. This server can be reached via SSH (only with publickey).

Some basic information about the server can be configured in the Lightsail dashboard. This includes the firewall.
We opened ports `22`, `80` and `443` to enable SSH, HTTP and HTTPS respectively.

### Server Info
OS: Ubuntu 18.04
user: `ubuntu`

### Continuous Deployment
Whenever a commit is merged into `master`, [`deploy.sh`](https://github.com/GipHouse/GiPHouse-Spring-2019/blob/master/resources/deploy.sh) is executed. This scripts runs on a Github Actions runner and gets secrets through the secrets settings of this repository.

This script does the following:
- Builds a new version of [the Docker image](https://hub.docker.com/r/giphouse/giphousewebsite) and pushes it to the Docker Hub Registry.
- Puts the right secrets into `docker-compose.yaml` and the database initialization file (`setup.sql`).
- Creates all necessary directories and files on the production server.
- Restarts the running docker containers using the new images.

### Setup steps
Some manual steps are taken to setup the server. These steps are not done in the deployment script, because these steps are only necessary once.

1. Add the SSH public keys of engineers to the authorized keys of the `ubuntu` user.
2. Disable SSH password login.
3. Install `docker`.
4. Install `nginx`.
5. Place the general `nginx` config (`nginx.conf`), the domain specific `nginx` config (`giphouse.conf`) and `dhparam.pem`.
6. Install `letsencrypt` and request a certificate using the `cerbot` `nginx` module.
