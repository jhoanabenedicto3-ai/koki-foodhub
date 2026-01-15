#!/usr/bin/env python
"""
Import script for Render deployment
Run on Render: python manage.py shell < import_render_data.py
Or run directly: python import_render_data.py
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

import django
django.setup()

from django.core.management import call_command

print("=" * 80)
print("IMPORTING DATA INTO RENDER DATABASE")
print("=" * 80)

files = [
    ('export_products.json', 'Products'),
    ('export_sales.json', 'Sales'),
    ('export_inventory.json', 'Inventory'),
]

for filename, name in files:
    if os.path.exists(filename):
        print(f"\n[*] Loading {name} from {filename}...")
        try:
            call_command('loaddata', filename)
            print(f"✓ {name} imported successfully")
        except Exception as e:
            print(f"✗ Error importing {name}: {e}")
    else:
        print(f"\n⚠ {filename} not found, skipping {name}")

print("\n" + "=" * 80)
print("IMPORT COMPLETE")
print("=" * 80)

from core.models import Product, Sale
print(f"✓ Total Products: {Product.objects.count()}")
print(f"✓ Total Sales: {Sale.objects.count()}")
print("\nVisit /product-forecast/ to see your data!")
