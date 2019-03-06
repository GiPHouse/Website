#!/usr/bin/env bash

set -e

until pg_isready --host="$POSTGRES_HOST" --username="$POSTGRES_USER" --quiet; do
    sleep 1;
done

chown --recursive www-data:www-data /giphouse/

cd /giphouse/src/website/

./manage.py compilescss
./manage.py collectstatic --no-input -v0 --ignore="*.scss"
./manage.py migrate --no-input

uwsgi --chdir=/giphouse/src/website \
    --module=giphousewebsite.wsgi:application \
    --master --pidfile=/tmp/project-master.pid \
    --socket=:8000 \
    --processes=5 \
    --uid=www-data --gid=www-data \
    --harakiri=20 \
    --post-buffering=16384 \
    --max-requests=5000 \
    --thunder-lock \
    --vacuum \
    --logfile-chown \
    --logto2=/giphouse/log/uwsgi.log
