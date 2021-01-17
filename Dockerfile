FROM python:3.9

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE giphousewebsite.settings.production
ENV PATH /root/.poetry/bin:${PATH}

ARG commit_hash="unknown commit hash"
ENV COMMIT_HASH=${commit_hash}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /giphouse/src/
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY poetry.lock pyproject.toml /giphouse/src/

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends postgresql-client && \
    rm --recursive --force /var/lib/apt/lists/* && \
    \
    mkdir --parents /giphouse/src/ && \
    mkdir --parents /giphouse/log/ && \
    mkdir --parents /giphouse/static/ && \
    chmod +x /usr/local/bin/entrypoint.sh && \
    \
    curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python && \
    poetry config --no-interaction --no-ansi virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev --extras "production"

COPY website /giphouse/src/website/
