"""
WSGI config with automatic migrations on startup
This ensures migrations run before the app starts
"""
import os
import sys
import django
from django.conf import settings
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Setup Django
django.setup()

# Run migrations on startup
print("\n" + "="*60)
print("🚀 KOKI FOODHUB - WSGI STARTUP")
print("="*60)

try:
    print("\n→ Running migrations...")
    call_command('migrate', verbosity=1, interactive=False)
    print("✅ Migrations successful")
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1)

# Create admin user if needed
try:
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username='admin').exists():
        print("\n→ Creating admin user...")
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        User.objects.create_superuser('admin', email, password)
        print(f"✅ Admin user created (password: {password})")
    else:
        print("\n✅ Admin user already exists")
except Exception as e:
    print(f"⚠️ Warning: {e}")

print("\n" + "="*60)
print("✅ STARTUP COMPLETE - App ready")
print("="*60 + "\n")

# Import the actual wsgi app
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
