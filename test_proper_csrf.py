#!/usr/bin/env python
"""
Test login with proper CSRF token extraction
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
import re

print("=" * 70)
print("TESTING LOGIN WITH PROPER CSRF EXTRACTION")
print("=" * 70)

client = Client(enforce_csrf_checks=True)

# Get login page
print("\n[1] GET /login/")
response = client.get('/login/')
print(f"    Status: {response.status_code}")

# Extract CSRF token - better regex
html = response.content.decode('utf-8')
csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
csrf_token = csrf_match.group(1) if csrf_match else None

if csrf_token:
    print(f"    CSRF Token extracted: {csrf_token[:30]}...")
else:
    print("    ERROR: Could not extract CSRF token")
    exit(1)

# Login
print("\n[2] POST /login/ with CSRF token")
data = {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token
}
response = client.post('/login/', data)
print(f"    Status: {response.status_code}")
if response.status_code == 302:
    print(f"    ✓ Redirect to: {response['Location']}")
else:
    print(f"    Status {response.status_code}")
    html_resp = response.content.decode('utf-8')
    if 'Invalid' in html_resp:
        print("    ✗ 'Invalid username or password' error")
    elif 'CSRF' in html_resp.upper():
        print("    ✗ CSRF validation error")
    else:
        print(f"    Response length: {len(html_resp)} bytes")

# Check session
print("\n[3] Session after login")
user_id = client.session.get('_auth_user_id')
print(f"    User ID in session: {user_id}")

if user_id:
    print("    ✓ Session authenticated")
else:
    print("    ✗ No user in session")

# Try to access dashboard
print("\n[4] GET / (dashboard)")
response = client.get('/')
print(f"    Status: {response.status_code}")

if response.status_code == 200:
    print("    ✓ Dashboard loaded successfully")
    # Check if it has dashboard content
    if 'dashboard' in response.content.decode('utf-8').lower():
        print("    ✓ Dashboard HTML found")
elif response.status_code == 302:
    print(f"    ✗ Redirected to: {response['Location']}")
    print("    This means the session authentication is not working")
