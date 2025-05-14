#!/bin/sh

echo "Ожидание PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL доступен!"

python manage.py makemigrations --noinput
python manage.py migrate --noinput

exec "$@"
