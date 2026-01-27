#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("=== Testing Admin Login ===\n")

# List all users
users = User.objects.all()
print(f"Total users in database: {users.count()}")
for u in users:
    print(f"  - Username: {u.username}, Active: {u.is_active}, Staff: {u.is_staff}")

print("\n=== Testing Authentication ===")

# Get admin user
admin = User.objects.filter(username='admin').first()
if admin:
    print(f"Admin user found: {admin.username}")
    print(f"  Is active: {admin.is_active}")
    print(f"  Check password 'admin123': {admin.check_password('admin123')}")
    
    # Try authenticating
    user = authenticate(username='admin', password='admin123')
    if user is not None:
        print(f"  Authentication successful!")
    else:
        print(f"  Authentication FAILED!")
        print(f"  Password hash: {admin.password[:50]}...")
else:
    print("No admin user found! Creating one...")
    admin = User.objects.create_user(username='admin', password='admin123', is_staff=True, is_superuser=True)
    print(f"Created admin user: {admin.username}")
    user = authenticate(username='admin', password='admin123')
    if user:
        print(f"Authentication test: SUCCESS")
    else:
        print(f"Authentication test: FAILED")
