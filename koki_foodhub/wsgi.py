"""
WSGI config for koki_foodhub project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Initialize Django
django.setup()

# CRITICAL: Run migrations and setup on first startup
print("\n" + "="*70)
print("🚀 DJANGO WSGI STARTUP - CHECKING DATABASE")
print("="*70)

try:
    from django.core.management import call_command
    from django.db import connection
    
    # Test database connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✅ Database connection OK")
    
    # Check if migrations table exists
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'django_migrations'
            );
        """)
        migrations_table_exists = cursor.fetchone()[0]
    
    if not migrations_table_exists:
        print("⚠️ Migrations table missing - running migrations...")
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed")
    else:
        print("✅ Migrations table exists - skipping migrations")
    
    # Ensure admin user exists
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        print("→ Creating admin user...")
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        User.objects.create_superuser('admin', email, password)
        print(f"✅ Admin user created!")
    
    print(f"📊 Database ready - {User.objects.count()} users, migrations OK")
    
except Exception as e:
    print(f"⚠️ Startup error (continuing anyway): {e}")
    import traceback
    traceback.print_exc()

print("="*70)
print("✅ WSGI STARTUP COMPLETE - App ready\n")
print("="*70 + "\n")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
