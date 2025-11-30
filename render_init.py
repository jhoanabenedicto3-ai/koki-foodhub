#!/usr/bin/env python
"""
Direct initialization for Render deployment
This runs BEFORE gunicorn starts to ensure database is ready
"""
import os
import sys
import django

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

print("\n" + "="*60)
print("🚀 RENDER INITIALIZATION SCRIPT")
print("="*60)

# Initialize Django
print("\n→ Initializing Django...")
try:
    django.setup()
    print("✅ Django initialized")
except Exception as e:
    print(f"❌ Django setup error: {e}")
    sys.exit(1)

# Now import Django components
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.db import connection

# Check database connection
print("\n→ Checking database connection...")
try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    print("✅ Database connection successful")
except Exception as e:
    print(f"❌ Database connection error: {e}")
    sys.exit(1)

# Run migrations
print("\n→ Running database migrations...")
try:
    call_command('migrate', verbosity=1)
    print("✅ Migrations completed successfully")
except Exception as e:
    print(f"❌ Migration error: {e}")
    sys.exit(1)

# Create admin user
print("\n→ Creating admin user...")
try:
    User = get_user_model()
    password = os.getenv('ADMIN_PASSWORD', 'admin123')
    email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
    
    if User.objects.filter(username='admin').exists():
        print("ℹ️  Admin user already exists")
    else:
        User.objects.create_superuser('admin', email, password)
        print(f"✅ Admin user created!")
        print(f"   Username: admin")
        print(f"   Email: {email}")
        print(f"   Password: {password}")
except Exception as e:
    print(f"⚠️  Warning - Admin user creation error: {e}")
    print("   (This is OK if the admin user already exists)")

print("\n" + "="*60)
print("✅ INITIALIZATION COMPLETE")
print("🚀 Web server starting...")
print("="*60 + "\n")

