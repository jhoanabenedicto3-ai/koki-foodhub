#!/usr/bin/env python
"""
Debug template rendering and check if csrf_token is in context
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
from django.template.loader import render_to_string
from django.middleware.csrf import get_token

client = Client()

# Get the login page
response = client.get('/login/')
print(f"Response status: {response.status_code}")
print(f"Response content type: {response.get('Content-Type', 'Not set')}")
print(f"Response has context: {response.context is not None}")

if response.context:
    print(f"Context keys: {list(response.context.keys())}")
    if 'csrf_token' in response.context:
        print(f"CSRF Token found: {response.context['csrf_token'][:20]}...")
    else:
        print("CSRF Token NOT in context")

# Print the actual HTML to see if csrf_token is being rendered
html_content = response.content.decode('utf-8')
if 'csrfmiddlewaretoken' in html_content:
    print("\n✓ Found 'csrfmiddlewaretoken' in HTML")
    # Find the line
    for i, line in enumerate(html_content.split('\n')):
        if 'csrfmiddlewaretoken' in line:
            print(f"  Line {i}: {line.strip()[:100]}")
else:
    print("\n✗ 'csrfmiddlewaretoken' NOT found in HTML")
    print("\nSearching for csrf in the form...")
    for i, line in enumerate(html_content.split('\n')):
        if 'csrf' in line.lower() or '<form' in line.lower():
            print(f"  Line {i}: {line.strip()[:100]}")
