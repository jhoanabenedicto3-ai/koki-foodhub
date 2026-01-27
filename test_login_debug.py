#!/usr/bin/env python
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Test with a known user
client = Client()

# Test 1: GET the login page
response = client.get('/login/')
print(f"[1] GET /login/ - Status: {response.status_code}")

# Test 2: POST with admin credentials
response = client.post('/login/', {
    'username': 'admin',
    'password': 'admin123'
})
print(f"[2] POST /login/ with admin/admin123 - Status: {response.status_code}")
print(f"    Redirect to: {response.url if hasattr(response, 'url') else response.get('Location', 'No Location header')}")

# Test 3: Check if user was actually authenticated
session = client.session
print(f"    Session user ID: {session.get('_auth_user_id', 'Not set')}")

# Test 4: Try with a different user
response = client.get('/')
print(f"[3] GET / (after login) - Status: {response.status_code}")

# Test 5: Check password directly
user = User.objects.get(username='admin')
print(f"\n[5] Direct authentication test:")
print(f"    User exists: {user}")
print(f"    User password hash: {user.password[:30]}...")
print(f"    Check password 'admin123': {user.check_password('admin123')}")
