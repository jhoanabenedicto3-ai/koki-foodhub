#!/usr/bin/env python
"""
Check the actual HTML response
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client

client = Client()
response = client.get('/login/')
html = response.content.decode('utf-8')

# Find the CSRF token in the HTML
print("Looking for CSRF token in HTML...")
print("=" * 70)

# Check different formats
patterns = [
    'csrfmiddlewaretoken',
    'csrf_token',
    'name="csrf',
    'value="'
]

lines = html.split('\n')
for i, line in enumerate(lines, 1):
    for pattern in patterns:
        if pattern.lower() in line.lower():
            print(f"Line {i}: {line.strip()}")

# Also print the form section
print("\n" + "=" * 70)
print("FORM SECTION:")
print("=" * 70)
in_form = False
for i, line in enumerate(lines, 1):
    if '<form' in line.lower():
        in_form = True
    if in_form:
        print(f"Line {i}: {line}")
    if '</form>' in line.lower():
        break
