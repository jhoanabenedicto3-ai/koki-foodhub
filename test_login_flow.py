#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

print("=== Testing Full Login Flow ===\n")

# Create client
client = Client()

# Ensure CSRF token works
print("1. Getting login page (CSRF token)...")
response = client.get('/login/')
print(f"   Status: {response.status_code}")

# Get CSRF token from cookie
csrf_token = response.cookies.get('csrftoken', {}).value
print(f"   CSRF Token: {csrf_token[:20] if csrf_token else 'NOT FOUND'}...")

# Attempt login
print("\n2. Attempting login with admin/admin123...")
response = client.post('/login/', {
    'username': 'admin',
    'password': 'admin123',
}, follow=True)

print(f"   Response status: {response.status_code}")
print(f"   Final URL: {response.redirect_chain}")

# Check if we're logged in
print(f"   User authenticated: {response.wsgi_request.user.is_authenticated if hasattr(response, 'wsgi_request') else 'N/A'}")

# Check for messages/errors
if hasattr(response, 'context') and response.context:
    messages_list = list(response.context.get('messages', []))
    if messages_list:
        print(f"   Messages: {[str(m) for m in messages_list]}")

print("\n3. Checking session...")
print(f"   Session data: {dict(client.session)}")
print(f"   Cookies: {list(client.cookies.keys())}")

# Test authenticated request
print("\n4. Testing authenticated request to dashboard...")
response = client.get('/')
print(f"   Status: {response.status_code}")
if response.status_code == 302:
    print(f"   Redirects to: {response.url}")
