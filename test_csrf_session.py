#!/usr/bin/env python
"""
Detailed debug of the login process
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User
from django.conf import settings

print("=" * 70)
print("LOGIN CONFIGURATION & SESSION DEBUG")
print("=" * 70)

print(f"\nDEBUG mode: {settings.DEBUG}")
print(f"LOGIN_URL: {settings.LOGIN_URL}")
print(f"LOGIN_REDIRECT_URL: {settings.LOGIN_REDIRECT_URL}")
print(f"SESSION_ENGINE: {settings.SESSION_ENGINE}")
print(f"SESSION_COOKIE_SECURE: {settings.SESSION_COOKIE_SECURE}")
print(f"SESSION_COOKIE_HTTPONLY: {settings.SESSION_COOKIE_HTTPONLY}")
print(f"SESSION_COOKIE_SAMESITE: {settings.SESSION_COOKIE_SAMESITE}")
print(f"CSRF_COOKIE_SAMESITE: {settings.CSRF_COOKIE_SAMESITE}")

# Create a test client with CSRF checks enabled (like a browser)
client = Client(enforce_csrf_checks=True)

print("\n" + "=" * 70)
print("TESTING LOGIN WITH CSRF ENFORCEMENT")
print("=" * 70)

# Step 1: Get login page to extract CSRF token
print("\n[1] GET /login/")
response = client.get('/login/')
print(f"    Status: {response.status_code}")

# Extract CSRF token from HTML
import re
csrf_match = re.search(r'csrfmiddlewaretoken["\']?\s*[=:]\s*["\']([^"\']+)', response.content.decode('utf-8'))
csrf_token = csrf_match.group(1) if csrf_match else None
print(f"    CSRF Token found: {csrf_token[:20] if csrf_token else 'NOT FOUND'}...")

if not csrf_token:
    print("    ERROR: CSRF token not found in login page!")
    import sys
    sys.exit(1)

# Step 2: Login with CSRF token
print("\n[2] POST /login/ with CSRF token")
response = client.post('/login/', {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token
})
print(f"    Status: {response.status_code}")
if response.status_code == 302:
    print(f"    Redirect to: {response['Location']}")
elif response.status_code == 200:
    print(f"    No redirect - returned 200")
    # Check for error messages
    if 'Invalid' in response.content.decode('utf-8'):
        print("    ⚠ 'Invalid' error message found in response")

# Step 3: Check session
print("\n[3] Session after login")
print(f"    Session dict keys: {list(client.session.keys())}")
print(f"    User ID: {client.session.get('_auth_user_id', 'NOT SET')}")

# Step 4: Access dashboard
print("\n[4] GET / (dashboard)")
response = client.get('/')
print(f"    Status: {response.status_code}")

if response.status_code == 302:
    print(f"    Redirected to: {response['Location']}")
elif response.status_code == 200:
    print(f"    ✓ Dashboard loaded")
