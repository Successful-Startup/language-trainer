#!/bin/bash
set -e  # Прерывание скрипта при ошибках

# echo "Create migrations"
# python manage.py makemigrations language_trainer_app
# echo "=================================="

echo "Migrate"
python manage.py migrate
echo "=================================="

echo "Start server"
python manage.py runserver 0.0.0.0:8000