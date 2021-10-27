#!/bin/sh
set -e

if [ "$WAITING_DATABASE" = true ]
then
    echo "Waiting for postgres..."

    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "PostgreSQL started"
fi

if [ "$MIGRATE" = true ]
then
    python manage.py migrate --noinput
fi

exec "$@"
