#!/bin/sh

# Exit on error
set -e

echo "📦 Running Django setup..."

echo "Waiting for Postgres..."
/wait-for-it.sh postgres:5432 --timeout=30 --strict -- echo "Postgres is up"
/wait-for-it.sh rabbitmq:5672 --timeout=20 --strict

# Run migrations
echo "📄 Running migrations..."
python manage.py migrate

# Collect static files (optional)
echo "🗃️ Collecting static files..."
python manage.py collectstatic --noinput

echo " Applying seeds of memeberships"
python manage.py seed_memberships --noinput

# Run the app (adjust if you're using gunicorn)
echo "🚀 Starting server..."
exec "$@"
