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
from django.conf import settings

def _masked_db_url(url: str) -> str:
    if not url:
        return "(none)"
    try:
        # mask password
        from urllib.parse import urlparse, urlunparse
        p = urlparse(url)
        if p.password:
            netloc = p.netloc.replace(p.password, '*****')
            return urlunparse((p.scheme, netloc, p.path, p.params, p.query, p.fragment))
    except Exception:
        pass
    return url

# CRITICAL: Run migrations and setup on first startup
print("\n" + "="*70)
print("🚀 DJANGO WSGI STARTUP - CHECKING DATABASE")
print("="*70)

# Log resolved database URL / host for easier debugging (mask password)
raw_db_url = os.getenv('DATABASE_URL')
print(f"→ DATABASE_URL: {_masked_db_url(raw_db_url)}")
db_host = None
try:
    db_host = settings.DATABASES.get('default', {}).get('HOST')
except Exception:
    db_host = None
print(f"→ Resolved DB HOST in settings: {db_host or '(not set)'}")

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
    print(f"⚠️ Startup error: {e}")
    import traceback
    traceback.print_exc()
    # If running in production (DEBUG=False) fail fast so the deployment shows
    # an error instead of starting a web process bound to localhost.
    try:
        if not settings.DEBUG:
            raise
    except Exception:
        # re-raise the original exception to abort startup
        raise

print("="*70)
print("✅ WSGI STARTUP COMPLETE - App ready\n")
print("="*70 + "\n")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
