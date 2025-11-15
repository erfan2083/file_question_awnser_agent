#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

# Wait for the database to be ready
echo "Waiting for database..."
# Use environment variables from docker-compose
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done
echo "Database ready!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files (though they are not served by Django in prod)
python manage.py collectstatic --noinput

# Start Gunicorn server
echo "Starting Gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4