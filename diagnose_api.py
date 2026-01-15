#!/usr/bin/env python
"""
Diagnostic script to check why Product Performance API returns no data
"""
import os
from dotenv import load_dotenv
load_dotenv()
os.environ['DEBUG'] = 'True'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, Sale
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta

print("\n" + "="*80)
print("PRODUCT PERFORMANCE API DIAGNOSTIC")
print("="*80)

# Check database connection
print("\n1. DATABASE CONNECTION:")
print("-" * 80)
try:
    print(f"✓ Django ORM connected")
    print(f"  Database: {django.db.connection.get_autocommit()}")
except Exception as e:
    print(f"✗ Connection error: {e}")

# Check raw data
print("\n2. RAW DATA CHECK:")
print("-" * 80)
products_count = Product.objects.count()
sales_count = Sale.objects.count()
print(f"Total products: {products_count}")
print(f"Total sales: {sales_count}")

if sales_count > 0:
    first_sale = Sale.objects.order_by('date').first()
    last_sale = Sale.objects.order_by('-date').first()
    print(f"Sales date range: {first_sale.date} to {last_sale.date}")
else:
    print("⚠ NO SALES DATA FOUND IN DATABASE")

# Check if forecasting service works
print("\n3. FORECASTING SERVICE CHECK:")
print("-" * 80)
try:
    from core.services.forecasting import product_forecast_summary
    print(f"✓ Forecasting service imported successfully")
    
    # Try to get forecast for first product
    if products_count > 0:
        first_product = Product.objects.first()
        print(f"  Testing with product: {first_product.name} (ID: {first_product.id})")
        
        try:
            summ = product_forecast_summary(first_product.id, horizons=(1, 7, 30), lookback_days=180)
            print(f"  ✓ Forecast generated:")
            print(f"    - 1-day forecast: {summ['horizons'].get('h_1', {}).get('forecast', 0)}")
            print(f"    - 7-day forecast: {summ['horizons'].get('h_7', {}).get('forecast', 0)}")
            print(f"    - 30-day forecast: {summ['horizons'].get('h_30', {}).get('forecast', 0)}")
            print(f"    - Series length: {len(summ.get('series', []))}")
        except Exception as e:
            print(f"  ✗ Forecast error: {e}")
except Exception as e:
    print(f"✗ Forecasting service import failed: {e}")

# Check specific product with sales
print("\n4. PRODUCTS WITH SALES:")
print("-" * 80)
products_with_sales = Product.objects.filter(sales__isnull=False).distinct()
count_with_sales = products_with_sales.count()
print(f"Products with sales: {count_with_sales}")

if count_with_sales > 0:
    for p in products_with_sales[:3]:
        sales_for_product = p.sales.count()
        total_units = p.sales.aggregate(total=Sum('units_sold'))['total'] or 0
        print(f"  - {p.name}: {sales_for_product} sales, {total_units} units")

# Check last 7 and 30 days
print("\n5. RECENT SALES CHECK:")
print("-" * 80)
today = timezone.localdate()
week_ago = today - timedelta(days=6)
month_ago = today - timedelta(days=29)

last_7_sales = Sale.objects.filter(date__gte=week_ago, date__lte=today).count()
last_30_sales = Sale.objects.filter(date__gte=month_ago, date__lte=today).count()

print(f"Today: {today}")
print(f"Last 7 days sales records: {last_7_sales}")
print(f"Last 30 days sales records: {last_30_sales}")

if last_7_sales > 0:
    print("✓ Recent sales data exists - API should return data")
elif last_30_sales > 0:
    print("⚠ Only older (>7 days) sales data exists - API will use those")
else:
    print("✗ NO RECENT SALES DATA - This might be why API returns 0 results")
    print("  Solution: Import recent sales data or create test sales")

print("\n" + "="*80 + "\n")
