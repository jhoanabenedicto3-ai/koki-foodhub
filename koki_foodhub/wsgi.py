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
print("[STARTUP] DJANGO WSGI STARTUP - CHECKING DATABASE")
print("="*70)

# Log resolved database URL / host for easier debugging (mask password)
raw_db_url = os.getenv('DATABASE_URL')
print(f"→ DATABASE_URL: {_masked_db_url(raw_db_url)}")

# Determine whether a remote DB is configured (not localhost/127.0.0.1)
remote_db_configured = False
try:
    from urllib.parse import urlparse
    if raw_db_url:
        p = urlparse(raw_db_url)
        db_hostname = (p.hostname or '').lower()
        if db_hostname and db_hostname not in ('localhost', '127.0.0.1'):
            remote_db_configured = True
except Exception:
    remote_db_configured = False

# Also inspect settings if available
db_host = None
try:
    db_host = settings.DATABASES.get('default', {}).get('HOST')
    if db_host and db_host not in ('localhost', '127.0.0.1'):
        remote_db_configured = True
except Exception:
    db_host = None

print(f"→ Resolved DB HOST in settings: {db_host or '(not set)'}")
print(f"→ Remote DB configured: {remote_db_configured}")

try:
    from django.core.management import call_command
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    
    # Test database connection
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("[OK] Database connection OK")
    
    # Check if migrations have been applied
    executor = MigrationExecutor(connection)
    plan = executor.migration_plan(executor.loader.graph.leaf_nodes())
    
    if plan:
        print(f"[WARNING] {len(plan)} pending migration(s) - running migrations...")
        call_command('migrate', verbosity=2)
        print("[OK] Migrations completed")
    else:
        print("[OK] Migrations already applied")
    
    # Collect static files in production
    if not os.getenv('DEBUG', 'True') == 'True':
        print("\n→ Collecting static files...")
        try:
            call_command('collectstatic', verbosity=1, interactive=False)
            print("[OK] Static files collected")
        except Exception as e:
            print(f"[WARNING] Static file collection warning: {e}")
    
    # Ensure admin user exists
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(username='admin').exists():
        print("→ Creating admin user...")
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        User.objects.create_superuser('admin', email, password)
        print(f"[OK] Admin user created!")
    
    print(f"[INFO] Database ready - {User.objects.count()} users")
    try:
        settings.DB_AVAILABLE = True
    except Exception:
        pass
    
except Exception as e:
    print(f"[ERROR] Startup error: {e}")
    import traceback
    traceback.print_exc()

    # Set a flag so the rest of the app can respond to DB unavailability.
    try:
        settings.DB_AVAILABLE = False
    except Exception:
        pass

    # Decide whether to abort startup on DB failure. By default we will continue
    # starting the web process so static pages and non-DB endpoints remain accessible.
    # Set ABORT_ON_DB_FAILURE=true in the environment to force an abort when the DB
    # is unreachable (useful for strict production safety checks).
    abort_env = os.getenv('ABORT_ON_DB_FAILURE', '').lower() == 'true'
    try:
        if abort_env:
            print("[ERROR] ABORT_ON_DB_FAILURE=true -- aborting startup due to DB failure.")
            raise
        else:
            print("[WARNING] DB check failed; continuing startup. Some features will remain limited until DB is available.")
    except Exception:
        # Re-raise the original exception to abort startup
        raise

print("="*70)
print("[OK] WSGI STARTUP COMPLETE - App ready\n")
print("="*70 + "\n")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
