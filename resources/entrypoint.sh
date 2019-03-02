#!/bin/env bash

set -e

until pg_isready -h "$POSTGRES_HOST" -U "$POSTGRES_USER"; do
    sleep 1;
done

cd /giphouse/src/website/

./manage.py collectstatic --no-input
./manage.py migrate --no-input
./manage.py compress --force

uwsgi --chdir=/giphouse/src/website \
    --module=giphousewebsite.wsgi:application \
    --env DJANGO_SETTINGS_MODULE=giphousewebsite.settings.production \
    --master --pidfile=/tmp/project-master.pid \
    --socket=0.0.0.0:8000 \
    --processes=5 \
    --uid=33 --gid=33 \
    --harakiri=60 \
    --max-requests=5000 \
    --vacuum \
    --daemonize=/giphouse/log/uwsgi.log
