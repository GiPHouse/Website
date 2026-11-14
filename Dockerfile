FROM python:3.14

ENV PYTHONUNBUFFERED 1
ENV DJANGO_SETTINGS_MODULE giphousewebsite.settings.production

ARG commit_hash="unknown commit hash"
ENV COMMIT_HASH=${commit_hash}

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

WORKDIR /giphouse/src/
COPY resources/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY pyproject.toml uv.lock /giphouse/src/

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install --yes --quiet --no-install-recommends \
        postgresql-client \
        curl && \
    rm --recursive --force /var/lib/apt/lists/* && \
    \
    mkdir --parents /giphouse/src/ && \
    mkdir --parents /giphouse/log/ && \
    mkdir --parents /giphouse/static/ && \
    chmod +x /usr/local/bin/entrypoint.sh && \
    \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    export PATH="/root/.local/bin:$PATH" && \
    uv sync --frozen --extra production

ENV PATH="/giphouse/src/.venv/bin:$PATH"
COPY website /giphouse/src/website/
