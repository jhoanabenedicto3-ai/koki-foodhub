#!/usr/bin/env python
"""
Test the complete login and dashboard flow
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()

print("=" * 70)
print("TESTING COMPLETE LOGIN FLOW")
print("=" * 70)

# Step 1: Get login page
print("\n[1] GET /login/")
response = client.get('/login/')
print(f"    Status: {response.status_code}")
assert response.status_code == 200, "Login page should return 200"

# Step 2: Login
print("\n[2] POST /login/ with credentials")
response = client.post('/login/', {
    'username': 'admin',
    'password': 'admin123'
}, follow=True)  # Follow redirects
print(f"    Status: {response.status_code}")
print(f"    Final URL: {response.request['PATH_INFO']}")
print(f"    Session has user: {'_auth_user_id' in client.session}")

# Step 3: Try to access dashboard directly
print("\n[3] GET / (dashboard)")
response = client.get('/')
print(f"    Status: {response.status_code}")
print(f"    Content type: {response.get('Content-Type', 'Not set')}")

if response.status_code == 200:
    html = response.content.decode('utf-8')
    if 'dashboard' in html.lower() or 'product' in html.lower():
        print(f"    ✓ Dashboard content found")
    else:
        print(f"    ✗ No dashboard content found")
        print(f"    HTML contains: {html[:500]}")
else:
    print(f"    ✗ Got status {response.status_code}")
    if 'Location' in response:
        print(f"    Redirected to: {response['Location']}")

# Step 4: Check session
print("\n[4] Session info")
print(f"    User ID in session: {client.session.get('_auth_user_id', 'Not set')}")
print(f"    Session expiry: {client.session.get('_session_expiry', 'Not set')}")

# Step 5: Try with explicit authentication
print("\n[5] Test with explicit session user set")
client2 = Client()
user = User.objects.get(username='admin')
client2.force_login(user)
response = client2.get('/')
print(f"    Status: {response.status_code}")
if response.status_code == 200:
    print(f"    ✓ Dashboard accessible with force_login")
else:
    print(f"    ✗ Dashboard returned {response.status_code}")
