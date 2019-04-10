poetry run flake8 --max-line-length=119 --exclude="migrations" website
poetry run pydocstyle --explain --add-ignore=D100,D104 --match-dir='(?!migrations).*'
poetry run python website/manage.py check --no-color
poetry run python website/manage.py makemigrations --no-input --check --dry-run
poetry run coverage run --omit=\"website/manage.py,website/giphousewebsite/wsgi.py,website/*/migrations/*\" --branch --source 'website' website/manage.py test
poetry run coverage report --show-missing --skip-covered --fail-under=93