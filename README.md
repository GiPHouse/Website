# GiPHouse website [![Build Status](https://travis-ci.com/GipHouse/GiPHouse-Spring-2019.svg?token=YrR2qkUGFcV8PDYmnPAG&branch=master)](https://travis-ci.com/GipHouse/GiPHouse-Spring-2019)

### Getting Started

1. Install Python 3.7 and [poetry](https://poetry.eustace.io/) (a Python dependency manager).
2. Clone this repository.
3. Run `poetry install` to install all dependencies into virtual environment.
4. Run `poetry shell` to enter the virtual environment.
5. Run `python website/manage.py migrate` to initialise the database.
5. Run `python website/manage.py createsuperuser` to create an admin account.
6. Run `python website/manage.py runserver` to start the local testing server.

### Loading Fixtures

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

### Running tests

The test suite can be run with the `manage.py` command. The following command can be executed to quickly run all the tests:

```bash
poetry run website/manage.py test
```

For more information about testing, see [docs/TESTING.md](/docs/TESTING.md).
