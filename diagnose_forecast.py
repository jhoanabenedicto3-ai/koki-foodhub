#!/usr/bin/env python
"""
Diagnostic script to check the product forecast data availability on Render.
This script inspects what's happening with the product forecast API.
"""
import os
import sys
import django

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

try:
    django.setup()
except Exception as e:
    print(f"ERROR: Could not set up Django: {e}")
    print("\nTo run this locally, first set DATABASE_URL:")
    print("  export DATABASE_URL='sqlite:///db.sqlite3'")
    print("  python diagnose_forecast.py")
    sys.exit(1)

from core.models import Product, Sale
from core.services.forecasting import product_forecast_summary, product_daily_series

print("=" * 80)
print("PRODUCT FORECAST DIAGNOSTIC")
print("=" * 80)

# 1. Check database connection and data
print("\n1. DATABASE INVENTORY:")
print(f"   Total Products: {Product.objects.count()}")
print(f"   Total Sales: {Sale.objects.count()}")
print(f"   Active Products: {Product.objects.filter(is_active=True).count()}")

# 2. List first few products
print("\n2. SAMPLE PRODUCTS:")
products = Product.objects.all()[:5]
if not products:
    print("   ⚠️  NO PRODUCTS FOUND IN DATABASE")
else:
    for p in products:
        print(f"   - {p.name} (ID: {p.id}, Active: {p.is_active}, Price: ${p.price})")

# 3. Check sales data
print("\n3. SALES DATA CHECK:")
if Sale.objects.count() == 0:
    print("   ⚠️  NO SALES RECORDS FOUND IN DATABASE")
    print("   This is the main reason forecasts are showing 0!")
else:
    recent_sales = Sale.objects.order_by('-date')[:5]
    for s in recent_sales:
        print(f"   - {s.product.name} ({s.units_sold} units) on {s.date}")

# 4. Test forecast for a single product
print("\n4. FORECAST TEST:")
if Product.objects.exists():
    p = Product.objects.first()
    print(f"\n   Testing forecast for: {p.name}")
    try:
        series = product_daily_series(p.id, lookback_days=90)
        print(f"   Daily series length: {len(series)} days")
        if series:
            total_units = sum(v for _, v in series)
            print(f"   Total units in 90 days: {total_units}")
            if total_units == 0:
                print("   ⚠️  NO SALES DATA FOR THIS PRODUCT")
            else:
                print(f"   Last 5 days: {series[-5:]}")
        
        summary = product_forecast_summary(p.id, horizons=(1, 7, 30))
        print(f"\n   Forecast Summary:")
        for h in [1, 7, 30]:
            h_key = f'h_{h}'
            forecast = summary['horizons'][h_key]['forecast']
            confidence = summary['horizons'][h_key]['confidence']
            print(f"     Horizon {h}d: {forecast} units (confidence: {confidence}%)")
    except Exception as e:
        print(f"   ERROR: {e}")
        import traceback
        traceback.print_exc()
else:
    print("   Cannot test - no products in database")

print("\n" + "=" * 80)
print("DIAGNOSIS SUMMARY:")
print("=" * 80)
product_count = Product.objects.count()
sales_count = Sale.objects.count()

if product_count == 0:
    print("❌ ISSUE: No products in database")
    print("   ACTION: Import products from CSV or add products manually")
elif sales_count == 0:
    print("❌ ISSUE: No sales data in database")
    print("   ACTION: Import sales data or create test sales records")
else:
    print("✓ Database contains products and sales")
    print("  The issue may be with:")
    print("    - Database URL not properly configured on Render")
    print("    - Authentication issues preventing API access")
    print("    - Frontend not properly handling the API response")

print("\n" + "=" * 80)
