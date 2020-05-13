#!/usr/bin/env bash

set -e

until pg_isready --host="${POSTGRES_HOST}" --username="${POSTGRES_USER}" --quiet; do
    sleep 1;
done

echo "Postgres database is up."

touch -a /giphouse/log/uwsgi.log
touch -a /giphouse/log/django.log

cd /giphouse/src/website/

./manage.py compilescss
./manage.py collectstatic --no-input -v0 --ignore="*.scss"
./manage.py migrate --no-input

cat << EOF | ./manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(github_id=${DJANGO_GITHUB_SYNC_SUPERUSER_ID}).exists():
  User.objects.create_superuser(github_id=${DJANGO_GITHUB_SYNC_SUPERUSER_ID})
EOF

chown --recursive www-data:www-data /giphouse/

echo "Starting uwsgi server."
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
    --logto2=/giphouse/log/uwsgi.log \
    --ignore-sigpipe \
    --ignore-write-errors \
    --disable-write-exception \
    --enable-threads
