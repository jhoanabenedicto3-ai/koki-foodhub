#!/usr/bin/env python
"""
Export local database and prepare for Render import
Run: python export_to_render.py
"""
import os
import json
import sys

# Use local SQLite database
os.environ['DEBUG'] = 'True'
os.environ['DJANGO_SETTINGS_MODULE'] = 'koki_foodhub.settings'

import django
django.setup()

from django.core import serializers
from core.models import Product, Sale, InventoryItem
from django.utils import timezone

print("=" * 80)
print("EXPORTING LOCAL DATABASE FOR RENDER")
print("=" * 80)

# Export products
print("\n[1/3] Exporting products...")
products = Product.objects.all()
products_json = serializers.serialize('json', products)
with open('export_products.json', 'w') as f:
    f.write(products_json)
print(f"✓ Exported {len(products)} products to export_products.json")

# Export sales
print("\n[2/3] Exporting sales...")
sales = Sale.objects.all()
sales_json = serializers.serialize('json', sales)
with open('export_sales.json', 'w') as f:
    f.write(sales_json)
print(f"✓ Exported {len(sales)} sales to export_sales.json")

# Export inventory items
print("\n[3/3] Exporting inventory...")
inventory = InventoryItem.objects.all()
inventory_json = serializers.serialize('json', inventory)
with open('export_inventory.json', 'w') as f:
    f.write(inventory_json)
print(f"✓ Exported {len(inventory)} inventory items to export_inventory.json")

print("\n" + "=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print("""
1. Upload the export files to Render:
   - Push them to your git repository (add to repo)
   - Or upload via Render file manager
   
2. On Render, run these commands:
   python manage.py loaddata export_products.json
   python manage.py loaddata export_sales.json  
   python manage.py loaddata export_inventory.json

3. Or run the import script on Render:
   python manage.py shell < import_local_data.py

4. Verify by visiting:
   https://your-app.onrender.com/forecast/debug/

Your product forecast should now show all {0} products with {1} sales records.
""".format(len(products), len(sales)))
