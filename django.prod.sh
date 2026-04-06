#!/bin/bash
set -e

echo "Migrate"
python manage.py migrate
echo "=================================="

echo "Collect static files"
python manage.py collectstatic --noinput
echo "=================================="

echo "Seed vocabulary"
python manage.py seed_vocabulary
echo "=================================="

echo "Start server"
exec gunicorn language_trainer_project.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --timeout 120