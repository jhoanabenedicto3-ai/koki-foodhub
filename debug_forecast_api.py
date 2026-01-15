#!/usr/bin/env python
"""Debug script to test the product_forecast_api response."""
import os
import sys
import django
from pathlib import Path

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
os.environ['DEBUG'] = 'True'

# For local SQLite, we don't need DATABASE_URL
sys.path.insert(0, str(Path(__file__).parent))
django.setup()

# Now test the API
from django.test import RequestFactory
from core.views import product_forecast_api
from core.models import Product, Sale
import json

print("=" * 60)
print("DEBUG: Product Forecast API Response")
print("=" * 60)

# Check database state
print(f"\nDatabase State:")
print(f"  Total Products: {Product.objects.count()}")
print(f"  Total Sales: {Sale.objects.count()}")

if Product.objects.count() > 0:
    print(f"  Sample Products:")
    for p in Product.objects.all()[:3]:
        print(f"    - {p.name} (ID:{p.id}, Active:{p.is_active})")

if Sale.objects.count() > 0:
    print(f"  Recent Sales:")
    for s in Sale.objects.order_by('-date')[:5]:
        print(f"    - {s.date}: {s.product.name} x{s.units_sold} units")

# Create a fake request
factory = RequestFactory()
request = factory.get('/product-forecast/api/', {
    'horizon': '7',
    'top': '100'
})

print(f"\nRequest: GET /product-forecast/api/?horizon=7&top=100")
print(f"Anonymous User: {request.user}")

# Call the API
response = product_forecast_api(request)
data = json.loads(response.content)

print(f"\nAPI Response Status: {response.status_code}")
print(f"Response Keys: {list(data.keys())}")

if 'error' in data:
    print(f"ERROR: {data['error']}")
    if 'details' in data:
        print(f"Details: {data['details']}")
else:
    print(f"Horizon: {data.get('horizon')}")
    print(f"Product Count: {len(data.get('top', []))}")
    print(f"Summary: {data.get('summary')}")
    
    top_products = data.get('top', [])
    if top_products:
        print(f"\nTop Products (first 5):")
        for i, p in enumerate(top_products[:5], 1):
            print(f"  {i}. {p.get('product')}")
            print(f"     Forecast (7d): {p.get('forecast_h')} units")
            print(f"     Confidence: {p.get('confidence')}%")
            print(f"     Last 7 Days: {p.get('last_7_days')} units")
            print(f"     Last 30 Days: {p.get('past_30_days')} units")
            print(f"     Growth Rate: {p.get('growth_rate')}%")
    else:
        print("\nNO PRODUCTS RETURNED!")
        print("Possible causes:")
        print("  1. No products in database")
        print("  2. product_forecast_summary() failing silently")
        print("  3. Queryset filtered to empty set")
