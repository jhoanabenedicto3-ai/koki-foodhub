#!/usr/bin/env python
"""
Test the product_forecast_api endpoint locally
Simulates what the dashboard will see when data is imported to Render
"""
import os
os.environ['DEBUG'] = 'True'
os.environ['DJANGO_SETTINGS_MODULE'] = 'koki_foodhub.settings'

import django
django.setup()

from django.test import RequestFactory
from core.views import product_forecast_api
import json

print("=" * 80)
print("TESTING PRODUCT FORECAST API ENDPOINT")
print("=" * 80)

# Create a mock request
factory = RequestFactory()
request = factory.get('/product-forecast/api/', {
    'horizon': '7',
    'top': '100'
})

# Add a mock user (required by @login_required)
from django.contrib.auth.models import User, AnonymousUser
request.user = User.objects.first() or AnonymousUser()

if isinstance(request.user, AnonymousUser):
    print("\nNo users in database - creating test user...")
    request.user = User.objects.create_user(username='test', password='test')

print(f"\nTesting with user: {request.user.username}")

try:
    response = product_forecast_api(request)
    data = json.loads(response.content)
    
    print(f"\nAPI Response Status: {response.status_code}")
    print(f"Products returned: {len(data.get('top', []))}")
    
    if 'top' in data and len(data['top']) > 0:
        print("\nTop 5 Products:")
        for p in data['top'][:5]:
            print(f"  - {p['product']}: {p['forecast_h']} units (conf: {p['confidence']:.1f}%)")
    
    summary = data.get('summary', {})
    print(f"\nSummary:")
    print(f"  Total Forecast (7d): {summary.get('total_forecast_units')} units")
    print(f"  Projected Revenue: ₱{summary.get('projected_revenue')}")
    
    # Simulate dashboard calculation
    top_products = data.get('top', [])[:15]
    if top_products:
        total_1d = sum(round(p['forecast_h'] / 7) for p in top_products)
        total_7d = sum(p['forecast_h'] for p in top_products)
        total_30d = sum(round(p['forecast_h'] * 4.3) for p in top_products)
        
        avg_conf_7d = sum(p['confidence'] for p in top_products[:10]) / min(10, len(top_products))
        avg_growth = sum(p['growth_rate'] for p in top_products[:10]) / min(10, len(top_products))
        
        print(f"\nDashboard would show:")
        print(f"  Next Day:   {total_1d} units")
        print(f"  Next Week:  {total_7d} units (confidence: {avg_conf_7d:.0f}%, trend: {avg_growth:.1f}%)")
        print(f"  Next Month: {total_30d} units")
    else:
        print("\nNo products with forecasts - data may not be imported yet")
        
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Once data is imported to Render, the dashboard will show these values!")
print("=" * 80)
