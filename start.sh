#!/bin/bash
set -e

echo "=========================================="
echo "🚀 RENDER DEPLOYMENT INITIALIZATION"
echo "=========================================="

# Change to project directory
cd /opt/render/project/src

# Run migrations
echo ""
echo "→ Running migrations..."
python manage.py migrate --verbosity 1 2>&1 || {
    echo "⚠️  Migration failed, but continuing..."
}

# Create admin user
echo ""
echo "→ Checking/creating admin user..."
python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
import os

if not User.objects.filter(username='admin').exists():
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
    User.objects.create_superuser('admin', email, password)
    print(f"✅ Admin user created!")
else:
    print("ℹ️  Admin user already exists")
END

echo ""
echo "=========================================="
echo "✅ INITIALIZATION COMPLETE"
echo "=========================================="
echo ""

# Start gunicorn
exec gunicorn \
    --bind 0.0.0.0:${PORT:-10000} \
    --workers 2 \
    --worker-class sync \
    --timeout 60 \
    --access-logfile - \
    --error-logfile - \
    koki_foodhub.wsgi:application
