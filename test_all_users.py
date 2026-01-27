#!/usr/bin/env python
"""
Test which users can login successfully
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

print("Testing login credentials...\n")

# Try common passwords for each user
test_passwords = ['admin123', 'password', 'password123', 'test', '123456', 'admin']

users = User.objects.all()
for user in users:
    print(f"User: {user.username}")
    found = False
    for pwd in test_passwords:
        auth_user = authenticate(username=user.username, password=pwd)
        if auth_user:
            print(f"  ✓ Works with password: '{pwd}'")
            found = True
            break
    if not found:
        print(f"  ✗ None of the common passwords work")
        # But let's check if the account is active
        print(f"    - Account active: {user.is_active}")
        print(f"    - Has usable password: {user.has_usable_password()}")
