#!/usr/bin/env python
"""
Remove duplicates from Render PostgreSQL database
Keeps the first record of each duplicate group
"""
import os
import sys
import django
from django.db.models import Count

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Get DATABASE_URL from command line or environment
if len(sys.argv) > 1:
    os.environ['DATABASE_URL'] = sys.argv[1]

django.setup()

from core.models import Product, Sale

print("\n" + "="*70)
print("🧹 REMOVING DUPLICATES FROM RENDER POSTGRESQL")
print("="*70)

# Before cleanup
print(f"\n📊 Database Before Cleanup:")
print(f"   Products: {Product.objects.count()}")
print(f"   Sales: {Sale.objects.count()}")

# Remove duplicate products
print(f"\n→ Removing duplicate products...")
dup_products = Product.objects.values('name', 'category').annotate(count=Count('id')).filter(count__gt=1)
removed_products = 0

for dup in dup_products:
    # Get all products matching this duplicate group
    products = Product.objects.filter(
        name=dup['name'],
        category=dup['category']
    ).order_by('id')
    
    # Keep the first one, delete the rest
    product_ids = list(products.values_list('id', flat=True))
    if len(product_ids) > 1:
        ids_to_delete = product_ids[1:]
        count = len(ids_to_delete)
        Product.objects.filter(id__in=ids_to_delete).delete()
        removed_products += count
        print(f"   ✓ {dup['name']} ({dup['category']}): removed {count} duplicates")

print(f"   ✅ Removed {removed_products} duplicate products")

# Remove duplicate sales
print(f"\n→ Removing duplicate sales...")
dup_sales = Sale.objects.values('product', 'date', 'units_sold', 'revenue').annotate(count=Count('id')).filter(count__gt=1)
removed_sales = 0

for dup in dup_sales:
    # Get all sales matching this duplicate group
    sales = Sale.objects.filter(
        product=dup['product'],
        date=dup['date'],
        units_sold=dup['units_sold'],
        revenue=dup['revenue']
    ).order_by('id')
    
    # Keep the first one, delete the rest
    sales_ids = list(sales.values_list('id', flat=True))
    if len(sales_ids) > 1:
        ids_to_delete = sales_ids[1:]
        count = len(ids_to_delete)
        Sale.objects.filter(id__in=ids_to_delete).delete()
        removed_sales += count

print(f"   ✅ Removed {removed_sales} duplicate sales")

# After cleanup
print(f"\n📊 Database After Cleanup:")
print(f"   Products: {Product.objects.count()}")
print(f"   Sales: {Sale.objects.count()}")

# Verify no more duplicates
print(f"\n🔍 Verifying no duplicates remain...")
dup_products_check = Product.objects.values('name', 'category').annotate(count=Count('id')).filter(count__gt=1)
dup_sales_check = Sale.objects.values('product', 'date', 'units_sold', 'revenue').annotate(count=Count('id')).filter(count__gt=1)

if not dup_products_check.exists() and not dup_sales_check.exists():
    print(f"   ✅ No duplicates found - database is clean!")
else:
    if dup_products_check.exists():
        print(f"   ⚠️  Still found {dup_products_check.count()} duplicate product groups")
    if dup_sales_check.exists():
        print(f"   ⚠️  Still found {dup_sales_check.count()} duplicate sale groups")

print("\n" + "="*70)
print("✅ DUPLICATE REMOVAL COMPLETE")
print("="*70 + "\n")
