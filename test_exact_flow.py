#!/usr/bin/env python
"""
Simulate exact browser behavior - login flow with detailed tracing
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
import re

print("=" * 80)
print("SIMULATING BROWSER LOGIN FLOW")
print("=" * 80)

# Create a new client (fresh browser session)
browser = Client()

# STEP 1: User opens login page
print("\n[STEP 1] User navigates to /login/")
response = browser.get('/login/')
print(f"  Response: {response.status_code} {response.reason_phrase}")

# Extract CSRF token
html = response.content.decode('utf-8')
csrf_match = re.search(r'name="csrfmiddlewaretoken"\s+value="([^"]+)"', html)
csrf_token = csrf_match.group(1) if csrf_match else None
print(f"  CSRF Token obtained: {csrf_token[:20] if csrf_token else 'MISSING'}...")

if not csrf_token:
    print("  ERROR: No CSRF token found!")
    exit(1)

# STEP 2: User fills form and submits
print("\n[STEP 2] User submits login form")
print("  POST /login/")
print(f"  Data: username=admin, password=admin123, csrf_token=***")

response = browser.post('/login/', {
    'username': 'admin',
    'password': 'admin123',
    'csrfmiddlewaretoken': csrf_token
})

print(f"  Response: {response.status_code} {response.reason_phrase}")
if response.status_code == 302:
    redirect_url = response['Location']
    print(f"  Redirect to: {redirect_url}")
    
    # STEP 3: Follow redirect
    print(f"\n[STEP 3] Browser follows redirect")
    print(f"  GET {redirect_url}")
    
    response = browser.get(redirect_url)
    print(f"  Response: {response.status_code} {response.reason_phrase}")
    
    # Check if page loaded
    if response.status_code == 200:
        page_html = response.content.decode('utf-8')
        
        # Check content
        if 'Dashboard' in page_html:
            print(f"  ✓ Dashboard page loaded")
        elif 'Login' in page_html:
            print(f"  ✗ Back to login page (auth failed)")
        else:
            print(f"  ? Unknown page")
    
elif response.status_code == 200:
    # No redirect, page reloaded
    page_html = response.content.decode('utf-8')
    if 'Invalid username or password' in page_html or 'error' in page_html.lower():
        print("  ✗ Login failed - error message shown")
        # Extract error
        error_match = re.search(r'Invalid[^<]*', page_html)
        if error_match:
            print(f"  Error: {error_match.group(0)}")
    else:
        print("  ? Page reloaded but no redirect")

# STEP 4: Check session
print(f"\n[STEP 4] Check authentication status")
session = browser.session
user_id = session.get('_auth_user_id')
print(f"  Session user_id: {user_id if user_id else 'NOT SET'}")

if user_id:
    print(f"  ✓ User is authenticated")
else:
    print(f"  ✗ User is NOT authenticated")

# STEP 5: Try to access dashboard
print(f"\n[STEP 5] Access dashboard")
response = browser.get('/')
print(f"  GET /")
print(f"  Response: {response.status_code} {response.reason_phrase}")

if response.status_code == 200:
    print(f"  ✓ Page loaded")
elif response.status_code == 302:
    print(f"  ✗ Redirected to: {response['Location']}")
    print(f"  This means authentication was lost!")
