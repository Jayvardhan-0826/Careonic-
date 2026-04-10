#!/usr/bin/env bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate --noinput

# Collect static files
python manage.py collectstatic --noinput

# Start the server with Gunicorn
gunicorn healthcare_mini.wsgi:application --bind 0.0.0.0:$PORT
