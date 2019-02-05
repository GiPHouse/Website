# GiPHouse website

### Getting Started

1. Install Python 3.7 and `poetry` (a Python dependency manager).
2. Clone this repository.
3. Run `poetry install` to install all dependencies into virtual environment.
4. Run `poetry shell` to enter the virtual environment.
5. Run `python website/manage.py migrate` to initialise the database.
5. Run `python webiste/manage.py createsuperuser` to create an admin account.
6. Run `python website/manage.py runserver` to start the local testing server.
