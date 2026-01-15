#!/usr/bin/env python
"""
Generate recent sales data for today and yesterday to make Product Performance table populate
"""
import os
from dotenv import load_dotenv
load_dotenv()
os.environ['DEBUG'] = 'True'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, Sale
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random

print("\n" + "="*80)
print("GENERATING RECENT SALES DATA FOR PRODUCT PERFORMANCE")
print("="*80 + "\n")

today = timezone.localdate()
yesterday = today - timedelta(days=1)

# Get products with existing sales
products_with_sales = Product.objects.filter(sales__isnull=False).distinct()[:20]

created_count = 0
for product in products_with_sales:
    # Create 3-5 sales per product for today and yesterday
    for date in [today, yesterday]:
        num_sales = random.randint(3, 6)
        units = random.randint(5, 30)
        price = product.price or Decimal('10.00')
        revenue = Decimal(str(units)) * price
        
        sale = Sale.objects.create(
            product=product,
            date=date,
            timestamp=timezone.now(),
            units_sold=units,
            revenue=revenue
        )
        created_count += 1
        print(f"✓ Created sale: {product.name} on {date} - {units} units")

print(f"\n{created_count} sales records created for today and yesterday")

# Verify
from django.db.models import Sum
week_ago = today - timedelta(days=6)
last_7_sales = Sale.objects.filter(date__gte=week_ago, date__lte=today).count()
print(f"\nVerification: {last_7_sales} sales in last 7 days")
print("\n" + "="*80)
print("✓ READY TO COMMIT - Recent sales data generated!")
print("="*80 + "\n")
