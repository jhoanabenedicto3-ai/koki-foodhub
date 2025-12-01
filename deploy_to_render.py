#!/usr/bin/env python
"""
Deploy local database data to Render PostgreSQL
Usage: python deploy_to_render.py <DATABASE_URL>
"""
import os
import sys
import django
import json
from pathlib import Path

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Get DATABASE_URL from command line or environment
if len(sys.argv) > 1:
    os.environ['DATABASE_URL'] = sys.argv[1]

django.setup()

from core.models import Product, Sale
from django.core.management import call_command

print("\n" + "="*70)
print("🚀 DEPLOYING DATA TO RENDER POSTGRESQL")
print("="*70)

# Check current counts
print(f"\n📊 Render Database Current State:")
print(f"   Products: {Product.objects.count()}")
print(f"   Sales: {Sale.objects.count()}")

# Load data
print(f"\n→ Loading data from deploy_data.json...")
try:
    call_command('loaddata', 'deploy_data.json', verbosity=2)
    print("\n✅ Data loaded successfully!")
except Exception as e:
    print(f"\n❌ Error loading data: {e}")
    sys.exit(1)

# Verify import
print(f"\n📊 Render Database After Import:")
print(f"   Products: {Product.objects.count()}")
print(f"   Sales: {Sale.objects.count()}")

# Check for duplicates
print(f"\n🔍 Checking for duplicates...")
from django.db.models import Count

# Find duplicate products
dup_products = Product.objects.values('name', 'category').annotate(count=Count('id')).filter(count__gt=1)
if dup_products.exists():
    print(f"   ⚠️  Found {dup_products.count()} duplicate product groups")
    for dup in dup_products:
        print(f"      - {dup['name']} ({dup['category']}): {dup['count']} copies")
else:
    print(f"   ✅ No duplicate products found")

# Find duplicate sales
dup_sales = Sale.objects.values('product', 'date', 'units_sold', 'revenue').annotate(count=Count('id')).filter(count__gt=1)
if dup_sales.exists():
    print(f"   ⚠️  Found {dup_sales.count()} duplicate sale groups")
else:
    print(f"   ✅ No duplicate sales found")

print("\n" + "="*70)
print("✅ DEPLOYMENT COMPLETE")
print("="*70 + "\n")
