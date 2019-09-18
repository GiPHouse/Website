#!/usr/bin/env bash

set -ve

docker login --username "${DOCKER_USERNAME}" --password "${DOCKER_PASSWORD}"
docker build --build-arg commit_hash="${COMMIT_HASH}" --tag "${DOCKER_IMAGE}" .
docker push "${DOCKER_IMAGE}"

mkdir "${HOME}/.ssh/"
chmod 700 "${HOME}/.ssh/"
echo "${SSH_PRIVATE_KEY}" > "${HOME}/.ssh/id_ed25519"
chmod 600 "${HOME}/.ssh/id_ed25519"

envsubst < resources/docker-compose.yaml.template > /tmp/out.tmp
mv /tmp/out.tmp resources/docker-compose.yaml

envsubst < resources/setup.sql.template > /tmp/out.tmp
mv /tmp/out.tmp resources/setup.sql

ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" /bin/bash << EOF
 sudo mkdir --parents "${DEPLOY_DIRECTORY}"
 sudo chown "${SSH_USER}":"${SSH_USER}" "${DEPLOY_DIRECTORY}"
 mkdir --parents "${DEPLOY_DIRECTORY}/database_init"
EOF

scp -o StrictHostKeyChecking=no resources/setup.sql "${SSH_USER}@${SSH_HOST}:${DEPLOY_DIRECTORY}/database_init/setup.sql"
scp -o StrictHostKeyChecking=no resources/docker-compose.yaml "${SSH_USER}@${SSH_HOST}:${DEPLOY_DIRECTORY}/docker-compose.yaml"

ssh -o StrictHostKeyChecking=no "${SSH_USER}@${SSH_HOST}" /bin/bash << EOF
 docker-compose --file "${DEPLOY_DIRECTORY}/docker-compose.yaml" config --quiet
 docker-compose --file "${DEPLOY_DIRECTORY}/docker-compose.yaml" pull
 docker-compose --file "${DEPLOY_DIRECTORY}/docker-compose.yaml" down
 docker-compose --file "${DEPLOY_DIRECTORY}/docker-compose.yaml" up -d --remove-orphans
EOF
