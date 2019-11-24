FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV DJANGO_SETTINGS_MODULE giphousewebsite.settings.production

ARG commit_hash="unknown commit hash"
ENV COMMIT_HASH=${commit_hash}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /giphouse/src/

RUN mkdir --parents /giphouse/src/ && \
    mkdir --parents /giphouse/log/ && \
    mkdir --parents /giphouse/static/ && \
    chown --recursive www-data:www-data /giphouse/

RUN apt-get update && \
    apt-get install --yes --no-install-recommends \
        postgresql-client \
    && rm --recursive --force /var/lib/apt/

COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

COPY poetry.lock /giphouse/src/
COPY pyproject.toml /giphouse/src/

RUN pip install --no-cache-dir poetry && \
    poetry config --no-interaction --no-ansi settings.virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev --extras "production" && \
    poetry cache:clear --no-interaction --no-ansi --all pypi

COPY website /giphouse/src/website/
