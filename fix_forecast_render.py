#!/usr/bin/env python
"""
RENDER DEPLOYMENT FIX: Import sales data to populate forecast
Run this on Render using the shell:
  render connect --database koki-foodhub-db --ssh
  cd /opt/render/project/src && python manage.py import_sales --limit 500
"""

import os
import sys
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.core.management import call_command

print("=" * 80)
print("FORECAST DATA IMPORT SCRIPT")
print("=" * 80)

# Step 1: Import products from CSV
print("\n[STEP 1/3] Importing products from pizzaplace.csv...")
try:
    call_command('import_products', '--csv', 'pizzaplace.csv', '--limit', '100')
    print("✓ Products imported successfully")
except Exception as e:
    print(f"⚠ Warning: Could not import products: {e}")

# Step 2: Import sales from CSV
print("\n[STEP 2/3] Importing sales data from pizzaplace.csv...")
try:
    call_command('import_sales', '--csv', 'pizzaplace.csv', '--limit', '500')
    print("✓ Sales data imported successfully")
except Exception as e:
    print(f"✗ Error importing sales: {e}")
    sys.exit(1)

# Step 3: Verify data
print("\n[STEP 3/3] Verifying data...")
from core.models import Product, Sale
product_count = Product.objects.count()
sale_count = Sale.objects.count()
print(f"✓ Products in database: {product_count}")
print(f"✓ Sales in database: {sale_count}")

if sale_count > 0:
    print("\n" + "=" * 80)
    print("SUCCESS!")
    print("=" * 80)
    print(f"✓ Forecast page should now show data with {product_count} products")
    print("  Navigate to: /product-forecast/")
    print("\nTo view diagnostic info: /forecast/debug/")
else:
    print("\nERROR: No sales data found. The import may have failed.")
    sys.exit(1)
