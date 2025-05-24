#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r convade_backend/requirements.txt

# Install additional production dependencies
pip install gunicorn psycopg2-binary whitenoise

# Collect static files
cd convade_backend
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

echo "Build completed successfully!" 