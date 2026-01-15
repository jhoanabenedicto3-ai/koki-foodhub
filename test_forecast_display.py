#!/usr/bin/env python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
os.environ['DEBUG'] = 'True'

import django
django.setup()

from core.models import Sale, Product
from core.services.forecasting import product_forecast_summary
from django.db.models import Sum
from datetime import timedelta
from django.utils import timezone

# Test forecast data
products = Product.objects.all()[:5]
print("=" * 60)
print("TESTING FORECAST DISPLAY")
print("=" * 60)

for p in products:
    try:
        summary = product_forecast_summary(p.id, horizons=(1, 7, 30), lookback_days=90)
        
        # Get sales data
        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=6)
        last_7 = Sale.objects.filter(product_id=p.id, date__gte=start_date).aggregate(total=Sum('units_sold'))['total'] or 0
        
        f1 = summary['horizons']['h_1']['forecast']
        f7 = summary['horizons']['h_7']['forecast']
        f30 = summary['horizons']['h_30']['forecast']
        conf1 = summary['horizons']['h_1']['confidence']
        conf7 = summary['horizons']['h_7']['confidence']
        conf30 = summary['horizons']['h_30']['confidence']
        
        print(f"\nProduct: {p.name}")
        print(f"  Last 7 days sales: {last_7}")
        print(f"  1-day forecast: {f1} (confidence: {conf1:.1f}%)")
        print(f"  7-day forecast: {f7} (confidence: {conf7:.1f}%)")
        print(f"  30-day forecast: {f30} (confidence: {conf30:.1f}%)")
    except Exception as e:
        print(f"Error for {p.name}: {e}")

print("\n" + "=" * 60)
print("FORECAST API TEST")
print("=" * 60)

# Test API response
from django.test import RequestFactory
from core.views import product_forecast_api

factory = RequestFactory()
request = factory.get('/product-forecast/api/?horizon=7&top=10')
response = product_forecast_api(request)
import json
data = json.loads(response.content)
print(f"API returned {len(data.get('top', []))} top products")
if data.get('top'):
    for product in data['top'][:3]:
        print(f"  - {product['product']}: forecast={product['forecast_h']}, confidence={product['confidence']:.1f}%")
