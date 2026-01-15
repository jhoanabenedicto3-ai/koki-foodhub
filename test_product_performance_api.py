#!/usr/bin/env python
"""
Test script to verify Product Performance API is working correctly
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

from django.test import Client
from django.contrib.auth.models import User
from core.models import Product, Sale
from django.utils import timezone
from datetime import timedelta
import json

print("\n" + "="*80)
print("PRODUCT PERFORMANCE API TEST")
print("="*80)

# Check sales data
print("\n1. CHECKING SALES DATA IN DATABASE:")
print("-" * 80)
total_sales = Sale.objects.count()
print(f"Total sales records: {total_sales}")

if total_sales > 0:
    first_sale = Sale.objects.order_by('date').first()
    last_sale = Sale.objects.order_by('-date').first()
    print(f"Date range: {first_sale.date} to {last_sale.date}")
    
    today = timezone.localdate()
    week_ago = today - timedelta(days=6)
    month_ago = today - timedelta(days=29)
    
    last_7_count = Sale.objects.filter(date__gte=week_ago, date__lte=today).count()
    last_30_count = Sale.objects.filter(date__gte=month_ago, date__lte=today).count()
    print(f"Sales in last 7 days: {last_7_count} records")
    print(f"Sales in last 30 days: {last_30_count} records")
else:
    print("⚠ WARNING: No sales data found in database!")

# Check products
print("\n2. CHECKING PRODUCTS:")
print("-" * 80)
total_products = Product.objects.count()
print(f"Total products: {total_products}")

products_with_sales = Product.objects.filter(sales__isnull=False).distinct().count()
print(f"Products with sales: {products_with_sales}")

if total_products > 0:
    sample = Product.objects.first()
    print(f"Sample product: {sample.name} (ID: {sample.id}, Category: {sample.category})")

# Check users
print("\n3. CHECKING AUTHENTICATION:")
print("-" * 80)
users = User.objects.count()
print(f"Total users: {users}")

if users == 0:
    print("⚠ WARNING: No users found! Creating test user...")
    user = User.objects.create_user(username='testuser', password='testpass123')
    print(f"✓ Created test user: {user.username}")
else:
    user = User.objects.first()
    print(f"Using existing user: {user.username}")

# Test API endpoint
print("\n4. TESTING API ENDPOINT:")
print("-" * 80)
client = Client()

# Try to login with existing user
login_success = client.login(username=user.username, password='admin' if user.username == 'admin' else 'testpass123')

if not login_success:
    print("⚠ Login with default credentials failed, trying to get API directly...")
else:
    print(f"✓ Logged in as {user.username}")

# Make API request
response = client.get('/product-forecast/api/?horizon=7&top=20')
print(f"API Response Status: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    print(f"✓ API returned valid JSON")
    print(f"  - Horizon: {data.get('horizon')}")
    print(f"  - Top products count: {len(data.get('top', []))}")
    print(f"  - Summary:")
    summary = data.get('summary', {})
    print(f"    - Total forecast units: {summary.get('total_forecast_units')}")
    print(f"    - Projected revenue: ₱{summary.get('projected_revenue', 0):.2f}")
    print(f"    - Product count: {summary.get('count')}")
    
    # Check first product data
    if data.get('top'):
        prod = data['top'][0]
        print(f"\n  Sample product data:")
        print(f"    - Product: {prod.get('product')}")
        print(f"    - Last 7 days: {prod.get('last_7_days')}")
        print(f"    - Last 30 days: {prod.get('past_30_days')}")
        print(f"    - Forecast (7d): {prod.get('forecast_h')}")
        print(f"    - Growth rate: {prod.get('growth_rate')}%")
        print(f"    - Confidence: {prod.get('confidence')}%")
else:
    print(f"✗ API Error: {response.status_code}")
    print(f"  Response: {response.content.decode()}")

print("\n" + "="*80)
print("TEST COMPLETE")
print("="*80 + "\n")
