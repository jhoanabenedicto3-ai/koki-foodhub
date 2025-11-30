#!/usr/bin/env python
"""
Direct initialization for Render deployment
This runs BEFORE gunicorn starts to ensure admin user exists
"""
import os
import sys
import django

# Setup Django first
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command

def initialize():
    print("\n" + "="*60)
    print("🚀 INITIALIZING RENDER DEPLOYMENT")
    print("="*60)
    
    # Migrations
    print("\n→ Running migrations...")
    try:
        call_command('migrate', verbosity=0)
        print("✅ Migrations successful")
    except Exception as e:
        print(f"❌ Migration error: {e}")
        return False
    
    # Create admin user
    print("→ Creating admin user...")
    try:
        User = get_user_model()
        password = os.getenv('ADMIN_PASSWORD', 'admin123')
        email = os.getenv('ADMIN_EMAIL', 'admin@koki-foodhub.com')
        
        if User.objects.filter(username='admin').exists():
            print("ℹ️ Admin user already exists")
        else:
            User.objects.create_superuser('admin', email, password)
            print(f"✅ Admin user created!")
            print(f"   Login: admin / {password}")
    except Exception as e:
        print(f"❌ Error creating admin: {e}")
        # Don't fail - continue anyway
    
    print("\n" + "="*60)
    print("✅ INITIALIZATION COMPLETE - Starting web server")
    print("="*60 + "\n")
    return True

if __name__ == '__main__':
    success = initialize()
    sys.exit(0 if success else 1)
