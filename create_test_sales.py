#!/usr/bin/env python
"""Create test sales data for new products."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, Sale
from django.utils import timezone
from datetime import timedelta
import random

# Get the products
fries = Product.objects.filter(name='fries').first()
carbonara = Product.objects.filter(name='carbonara').first()

if not fries or not carbonara:
    print("❌ Products not found. Checking database...")
    all_products = Product.objects.all()
    print(f"Found {all_products.count()} products:")
    for p in all_products[:10]:
        print(f"  - {p.name} (id={p.id})")
else:
    print(f"✅ Found products: {fries.name} (id={fries.id}), {carbonara.name} (id={carbonara.id})")
    
    # Create 30 days of sales history for both products
    today = timezone.now().date()
    created_count = 0
    
    for days_back in range(30):
        date = today - timedelta(days=days_back)
        
        # Fries: 5-15 units per day
        fries_units = random.randint(5, 15)
        fries_price = float(fries.price or 100)
        Sale.objects.get_or_create(
            product=fries,
            date=date,
            defaults={
                'units_sold': fries_units,
                'revenue': fries_units * fries_price,
                'created_at': timezone.now()
            }
        )
        created_count += 1
        
        # Carbonara: 3-10 units per day
        carbonara_units = random.randint(3, 10)
        carbonara_price = float(carbonara.price or 150)
        Sale.objects.get_or_create(
            product=carbonara,
            date=date,
            defaults={
                'units_sold': carbonara_units,
                'revenue': carbonara_units * carbonara_price,
                'created_at': timezone.now()
            }
        )
        created_count += 1
    
    print(f"✅ Created {created_count} sales records for the past 30 days")
    
    # Verify
    fries_sales = Sale.objects.filter(product=fries).count()
    carbonara_sales = Sale.objects.filter(product=carbonara).count()
    print(f"✅ Fries sales records: {fries_sales}")
    print(f"✅ Carbonara sales records: {carbonara_sales}")
    print(f"\n✅ Products are now ready for forecasting!")
    print(f"🎯 Go to /product-forecast/ to see the Product Performance table with data")
