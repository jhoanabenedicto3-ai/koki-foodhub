#!/usr/bin/env python
"""
Check if dashboard page has any errors or issues
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.contrib.auth.models import User

client = Client()

# Login
client.login(username='admin', password='admin123')

# Get dashboard
response = client.get('/')
html = response.content.decode('utf-8')

print("=" * 70)
print("DASHBOARD PAGE ANALYSIS")
print("=" * 70)

print(f"\nStatus: {response.status_code}")
print(f"Content-Type: {response.get('Content-Type')}")
print(f"HTML length: {len(html)} bytes")

# Check for common error indicators
error_indicators = [
    ('ERROR', 'ERROR keyword'),
    ('Exception', 'Exception thrown'),
    ('Traceback', 'Python traceback'),
    ('500', 'HTTP 500 error'),
    ('404', 'HTTP 404 error'),
    ('no such', 'Database error'),
    ('OperationalError', 'Operational error'),
]

print("\nError check:")
for indicator, desc in error_indicators:
    if indicator in html:
        print(f"  ⚠ Found: {desc}")

# Check for key content
content_checks = [
    ('KUYA', 'Logo/Brand'),
    ('Dashboard', 'Dashboard title'),
    ('product', 'Product references'),
    ('inventory', 'Inventory section'),
    ('sales', 'Sales section'),
    ('logout', 'Logout link (auth working)'),
]

print("\nContent check:")
for check, desc in content_checks:
    if check.lower() in html.lower():
        print(f"  ✓ Found: {desc}")
    else:
        print(f"  ✗ Missing: {desc}")

# Check HTML structure
print("\nHTML structure:")
print(f"  - Has <html>: {'<html' in html.lower()}")
print(f"  - Has <body>: {'<body' in html.lower()}")
print(f"  - Has <form>: {'<form' in html.lower()}")

# Check for the main navigation/dashboard content
if '<main' in html.lower() or '<div class' in html:
    print(f"  ✓ Has main content areas")

# Print first 1000 chars to see what's being rendered
print("\nFirst 1000 characters of response:")
print("-" * 70)
print(html[:1000])
print("-" * 70)
