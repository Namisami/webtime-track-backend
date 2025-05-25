#!/bin/sh

until nc -z db 5432; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

python manage.py migrate --noinput
python manage.py createsuperuser --noinput --email admin@admin.admin || true

exec "$@"
