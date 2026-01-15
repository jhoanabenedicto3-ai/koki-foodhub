#!/usr/bin/env python
"""Check if we can access database locally."""
import os
import django

# Force DEBUG and use SQLite
os.environ['DEBUG'] = 'True'
os.environ.pop('DATABASE_URL', None)  # Remove this if it exists
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Fix: Configure Django apps before importing models
django.setup()

from core.models import Product, Sale
from django.utils import timezone

print("Database Check:")
print(f"Products: {Product.objects.count()}")
print(f"Sales: {Sale.objects.count()}")

if Sale.objects.count() > 0:
    recent = Sale.objects.order_by('-date').first()
    today = timezone.localdate()
    print(f"\nMost recent sale: {recent.date}")
    print(f"Today's date: {today}")
    print(f"Days difference: {(today - recent.date).days}")
