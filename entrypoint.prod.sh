#!/bin/sh

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"

    echo "Running migrations"
    python manage.py migrate
    echo "Migrations complete"

    echo "Collecting static files"
    python manage.py collectstatic --noinput
fi

exec "$@"