#!/bin/bash
set -e

echo "=========================================="
echo "🚀 RENDER DEPLOYMENT INITIALIZATION"
echo "=========================================="

# Change to project directory  
cd /opt/render/project/src

# Run migrations with explicit verbose output
echo ""
echo "→ Running migrations..."
python manage.py migrate --verbosity 2

# Create admin user
echo ""
echo "→ Checking/creating admin user..."
python << END
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth import get_user_model
User = get_user_model()

admin_user = User.objects.filter(username='admin').first()
if admin_user:
    print("✅ Admin user already exists")
else:
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
    User.objects.create_superuser('admin', email, password)
    print("✅ Admin user created!")

print(f"📊 Total users in database: {User.objects.count()}")
END

echo ""
echo "=========================================="
echo "✅ INITIALIZATION COMPLETE"
echo "=========================================="
echo ""

# Choose server: gunicorn (default) or Django runserver (when USE_RUNSERVER=true and DEBUG=true)
# Prevent accidental use of runserver in production by requiring DEBUG=true
if [ "${USE_RUNSERVER:-false}" = "true" ]; then
    DEBUG_LOWER=$(echo "${DEBUG:-false}" | tr '[:upper:]' '[:lower:]')
    if [ "$DEBUG_LOWER" != "true" ]; then
        echo "→ ERROR: runserver requires DEBUG=true for safety. Set DEBUG=true and USE_RUNSERVER=true to enable. Aborting."
        exit 1
    fi

    echo "→ Starting Django development server (runserver) for debugging"
    # Bind to the port Render provides; disable the autoreloader to avoid issues in container
    exec python manage.py runserver 0.0.0.0:${PORT:-8000} --noreload
else
    echo "→ Starting gunicorn"
    exec gunicorn \
        --bind 0.0.0.0:${PORT:-10000} \
        --workers 2 \
        --worker-class sync \
        --timeout 60 \
        --access-logfile - \
        --error-logfile - \
        koki_foodhub.wsgi:application
fi
