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
    from django.db.migrations.executor import MigrationExecutor
    
    # Test database connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✅ Database connection OK")
    
    # Check if migrations have been applied
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    
    if plan:
        print(f"⚠️ {len(plan)} pending migration(s) - running migrations...")
        call_command('migrate', verbosity=2)
        print("✅ Migrations completed")
    else:
        print("✅ Migrations already applied")
    
    # Collect static files in production
    if not os.getenv('DEBUG', 'True') == 'True':
        print("\n→ Collecting static files...")
        try:
            call_command('collectstatic', verbosity=1, interactive=False)
            print("✅ Static files collected")
        except Exception as e:
            print(f"⚠️ Static file collection warning: {e}")
    
    # Ensure admin user exists
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        print("→ Creating admin user...")
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        User.objects.create_superuser('admin', email, password)
        print(f"✅ Admin user created!")
    
    print(f"📊 Database ready - {User.objects.count()} users")
    
except Exception as e:
    print(f"⚠️ Startup error (continuing anyway): {e}")
    import traceback
    traceback.print_exc()

print("="*70)
print("✅ WSGI STARTUP COMPLETE - App ready\n")
print("="*70 + "\n")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
