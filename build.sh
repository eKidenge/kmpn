# 1. Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# 2. Load initial data (optional)
if [ -f "load_data.py" ]; then
    echo "Loading initial data..."
    python load_data.py
fi

# 3. Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# 4. Create superuser
echo "Creating superuser..."
python manage.py shell << EOF
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kmpn.settings')

from django.contrib.auth import get_user_model

User = get_user_model()

# Remove existing admin if present
User.objects.filter(email='admin@kmpn.org').delete()

# Create superuser
User.objects.create_superuser(
    email='admin@kmpn.org',
    password='Admin@123'
)

print("Superuser created")
print("   Email: admin@kmpn.org")
print("   Password: Admin@123")

# Optional demo user
User.objects.filter(email='member@kmpn.org').delete()

User.objects.create_user(
    email='member@kmpn.org',
    password='Member@123'
)

print("Demo user created")
print("   Email: member@kmpn.org")
print("   Password: Member@123")
EOF

echo "KMPN build completed successfully!"