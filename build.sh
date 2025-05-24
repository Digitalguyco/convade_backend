#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Install additional production dependencies
pip install gunicorn psycopg2-binary whitenoise

# Set Django settings for build commands
export DJANGO_SETTINGS_MODULE=convade_backend.settings.production

# Run migrations
python manage.py migrate

# Create cache table for database caching (fallback when Redis is not available)
python manage.py createcachetable

# Collect static files
python manage.py collectstatic --noinput

echo "Build completed successfully!" 