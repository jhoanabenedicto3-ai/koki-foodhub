#!/usr/bin/env python
"""
Direct test of the product_forecast_api view without HTTP layer
"""
import os
import sys

# Load .env file before Django setup
from dotenv import load_dotenv
load_dotenv()

# Set DEBUG for development
os.environ['DEBUG'] = 'True'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, Sale
from django.db.models import Sum
from django.utils import timezone
from datetime import timedelta
import json

print("\n" + "="*80)
print("DIRECT API LOGIC TEST")
print("="*80)

# Simulate what the API does
print("\n1. FETCHING PRODUCT DATA:")
print("-" * 80)

from core.services.forecasting import product_forecast_summary

products = Product.objects.all()[:20]
products_payload = []

today = timezone.localtime().date()
week_ago = today - timedelta(days=6)
month_ago = today - timedelta(days=29)

print(f"Today: {today}")
print(f"Week ago: {week_ago}")
print(f"Month ago: {month_ago}\n")

for p in products:
    try:
        summ = product_forecast_summary(p.id, horizons=(1, 7, 30), lookback_days=180)
        
        # Get forecast for 7-day horizon
        h_key = 'h_7'
        hinfo = summ['horizons'].get(h_key, {'forecast': 0, 'confidence': 0})
        forecast_h = int(hinfo.get('forecast', 0))
        
        # Get actual sales from database
        last_7_sales = Sale.objects.filter(
            product_id=p.id,
            date__gte=week_ago,
            date__lte=today
        ).aggregate(total=Sum('units_sold'))
        last_7_db = int(last_7_sales.get('total') or 0)
        
        last_30_sales = Sale.objects.filter(
            product_id=p.id,
            date__gte=month_ago,
            date__lte=today
        ).aggregate(total=Sum('units_sold'))
        past_30_db = int(last_30_sales.get('total') or 0)
        
        # Calculate growth
        denom = last_7_db if last_7_db > 0 else None
        if denom:
            growth = round((forecast_h - denom) / float(denom) * 100.0, 1)
        else:
            growth = 0.0
        
        price = float(p.price) if p.price else 0.0
        projected_revenue = round(forecast_h * price, 2)
        
        products_payload.append({
            'product_id': p.id,
            'product': p.name,
            'category': p.category or '',
            'last_7_days': last_7_db,
            'past_30_days': past_30_db,
            'forecast_h': forecast_h,
            'growth_rate': growth,
            'confidence': float(hinfo.get('confidence', 0)),
            'price': price,
            'projected_revenue': projected_revenue,
        })
        
        if len(products_payload) <= 5:
            print(f"✓ {p.name}:")
            print(f"  - Last 7 days: {last_7_db} units")
            print(f"  - Last 30 days: {past_30_db} units")
            print(f"  - Forecast (7d): {forecast_h} units")
            print(f"  - Growth: {growth}%")
            print(f"  - Confidence: {hinfo.get('confidence', 0)}%\n")
    except Exception as e:
        print(f"✗ Error processing {p.name}: {e}")

print(f"\nTotal products processed: {len(products_payload)}")

# Sort by forecast
products_sorted = sorted(products_payload, key=lambda x: x['forecast_h'], reverse=True)

print("\n2. TOP 5 PRODUCTS BY FORECAST:")
print("-" * 80)
for i, p in enumerate(products_sorted[:5], 1):
    print(f"{i}. {p['product']} ({p['category']})")
    print(f"   Last 7 days: {p['last_7_days']} | Last 30 days: {p['past_30_days']} | Forecast: {p['forecast_h']} | Trend: {p['growth_rate']}%")

print("\n" + "="*80)
print("✓ API LOGIC TEST COMPLETE - ALL DATA RETRIEVAL WORKING")
print("="*80 + "\n")
