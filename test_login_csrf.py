#!/usr/bin/env python
"""
Test the login as it would be done via an HTTP request
"""
import os
import django
import json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

# Recreate a real browser session
client = Client(enforce_csrf_checks=True)

# Step 1: GET the login page to get CSRF token
response = client.get('/login/')
csrf_token = response.context['csrf_token'] if response.context else None
print(f"[1] GET /login/")
print(f"    Status: {response.status_code}")
print(f"    CSRF Token: {csrf_token[:20] if csrf_token else 'Not found'}...")

# Step 2: Try to login with CSRF token
if csrf_token:
    response = client.post('/login/', {
        'username': 'admin',
        'password': 'admin123',
        'csrfmiddlewaretoken': csrf_token
    })
    print(f"\n[2] POST /login/ with CSRF")
    print(f"    Status: {response.status_code}")
    print(f"    Redirects to: {response.url if hasattr(response, 'url') else response.get('Location', 'No redirect')}")
else:
    print("ERROR: Could not get CSRF token")

# Step 3: List all users and their usernames
print(f"\n[3] Available users for testing:")
users = User.objects.all()
for user in users:
    print(f"    - {user.username}")
