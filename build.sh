#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input

python manage.py migrate
python manage.py shell -c 'import os; from django.contrib.auth import get_user_model; User = get_user_model(); u, _ = User.objects.get_or_create(username=os.environ["DJANGO_SUPERUSER_USERNAME"]); u.email=os.environ["DJANGO_SUPERUSER_EMAIL"]; u.is_staff=True; u.is_superuser=True; u.set_password(os.environ["DJANGO_SUPERUSER_PASSWORD"]); u.save()'