#!/bin/sh

# Exit on error
set -e

echo "📦 Running Django setup..."

echo "Waiting for Postgres..."
/wait-for-it.sh db:5432 --timeout=30 --strict -- echo "Postgres is up"

# Run migrations
echo "📄 Running migrations..."
python manage.py migrate

# Collect static files (optional)
echo "🗃️ Collecting static files..."
python manage.py collectstatic --noinput

# Run the app (adjust if you're using gunicorn)
echo "🚀 Starting server..."
exec "$@"
