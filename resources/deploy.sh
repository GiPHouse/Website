#!/usr/bin/env bash

set -ve

# Enable aliases in non-interactive bash shells.
shopt -s expand_aliases

if [[ "true" != "${TRAVIS}" ]]; then
    echo "This should only be run by Travis CI!"
    exit 1
fi

# Set production server variables
PRODUCTION_IP="35.157.118.162"
PRODUCTION_SSH_HOST_PUBLIC="${PRODUCTION_IP} ecdsa-sha2-nistp256 AAAAE2VjZHNhLXNoYTItbmlzdHAyNTYAAAAIbmlzdHAyNTYAAABBBNtS0/bWyMVsg0bLjU3GbwwuPSA1VFiWoRL5a71k7PsheZMIh+KDtdvE+miqAGMmKdms4LeT9nT1zyR5VMwr08A="
PRODUCTION_SSH_URI="${SSH_DEPLOY_USER}@${PRODUCTION_IP}"

# Set directory variables
DEPLOY_DIRECTORY="/usr/local/giphouse"
DATABASE_DIRECTORY="${DEPLOY_DIRECTORY}/db"
DATABASE_INIT_DIRECTORY="${DEPLOY_DIRECTORY}/db_init"

# Set file path variables
DOCKER_COMPOSE_PATH="${DEPLOY_DIRECTORY}/docker-compose.yaml"
DOCKER_COMPOSE_PATH_LOCAL="resources/docker-compose.yaml.template"
DATABASE_INIT_SQL_PATH="${DATABASE_INIT_DIRECTORY}/setup.sql"
DATABASE_INIT_SQL_PATH_LOCAL="resources/setup.sql.template"

DOCKER_IMAGE="giphouse/giphousewebsite:latest"

alias run='ssh ${PRODUCTION_SSH_URI}'

# Build and push docker image.
echo "${DOCKER_PASSWORD}" | docker login --username "${DOCKER_USERNAME}" --password-stdin
docker build --build-arg commit_hash="${TRAVIS_COMMIT}" --tag "${DOCKER_IMAGE}" .
docker push "${DOCKER_IMAGE}"

# Add production host key to known hosts.
echo "${PRODUCTION_SSH_HOST_PUBLIC}" >> ~/.ssh/known_hosts

# Create necessary directories.
run sudo mkdir --parents "${DEPLOY_DIRECTORY}"
run sudo chown "${SSH_DEPLOY_USER}":"${SSH_DEPLOY_USER}" "${DEPLOY_DIRECTORY}"
run mkdir --parents "${DATABASE_INIT_DIRECTORY}"

# Set variables in database init file.
# We use @ instead of / as sed separator, because / is used in paths.
sed --in-place='' \
    --expression "s@{{POSTGRES_NAME}}@${POSTGRES_NAME}@" \
    --expression "s@{{POSTGRES_USER}}@${POSTGRES_USER}@" \
    --expression "s@{{POSTGRES_PASSWORD}}@${POSTGRES_PASSWORD}@" \
    "${DATABASE_INIT_SQL_PATH_LOCAL}"

# Set environment variables in docker-compose.yaml.
sed --in-place='' \
    --expression "s@{{DEPLOY_DIRECTORY}}@${DEPLOY_DIRECTORY}@" \
    --expression "s@{{DATABASE_DIRECTORY}}@${DATABASE_DIRECTORY}@" \
    --expression "s@{{DATABASE_INIT_DIRECTORY}}@${DATABASE_INIT_DIRECTORY}@" \
    --expression "s@{{DJANGO_SECRET_KEY}}@${DJANGO_SECRET_KEY}@" \
    --expression "s@{{POSTGRES_NAME}}@${POSTGRES_NAME}@" \
    --expression "s@{{POSTGRES_USER}}@${POSTGRES_USER}@" \
    --expression "s@{{POSTGRES_PASSWORD}}@${POSTGRES_PASSWORD}@" \
    --expression "s@{{GITHUB_CLIENT_ID}}@${GITHUB_CLIENT_ID}@" \
    --expression "s@{{GITHUB_CLIENT_SECRET}}@${GITHUB_CLIENT_SECRET}@" \
    --expression "s@{{DOCKER_IMAGE}}@${DOCKER_IMAGE}@" \
    "${DOCKER_COMPOSE_PATH_LOCAL}"

# Upload config files.
scp "${DATABASE_INIT_SQL_PATH_LOCAL}" "${PRODUCTION_SSH_URI}:${DATABASE_INIT_SQL_PATH}"
scp "${DOCKER_COMPOSE_PATH_LOCAL}" "${PRODUCTION_SSH_URI}:${DOCKER_COMPOSE_PATH}"

# Test docker-compose.yaml syntax.
run docker-compose --file "${DOCKER_COMPOSE_PATH}" config --quiet

# Pull and restart dockers.
run sudo docker-compose --file "${DOCKER_COMPOSE_PATH}" pull
run sudo docker-compose --file "${DOCKER_COMPOSE_PATH}" down
run sudo docker-compose --file "${DOCKER_COMPOSE_PATH}" up -d --remove-orphans
