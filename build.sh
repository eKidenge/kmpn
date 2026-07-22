#!/usr/bin/env bash
set -o errexit

echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Applying database migrations..."
python manage.py migrate

echo "Loading initial data..."
if [ -f "load_data.py" ]; then
    python manage.py shell < load_data.py
fi

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(email='admin@kmpn.org').exists():
    User.objects.create_superuser(
        email='admin@kmpn.org',
        password='Admin@123'
    )
    print("Superuser created")
else:
    print("Superuser already exists")
EOF

echo "KMPN build completed successfully!"