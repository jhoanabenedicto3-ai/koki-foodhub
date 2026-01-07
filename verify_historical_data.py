#!/usr/bin/env python
"""
Verification script to compare historical data between sales_dashboard and forecast chart.
This checks that aggregate_sales() returns revenue matching the sales dashboard data.
"""
import os

# Set required environment variables BEFORE importing Django
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('SECRET_KEY', 'dev-secret-key')
os.environ.setdefault('DATABASE_URL', 'sqlite:///db.sqlite3')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

import django
django.setup()

from datetime import date, timedelta
from django.db.models import Sum
from core.models import Sale
from core.services.forecasting import aggregate_sales

# Test date range
today = date.today()
start_date = today - timedelta(days=6)

print("=" * 80)
print("HISTORICAL DATA VERIFICATION")
print("=" * 80)
print(f"Date range: {start_date} to {today}\n")

# Get data from aggregate_sales (forecast chart)
print("1. Forecast Chart Data (from aggregate_sales):")
daily_series = aggregate_sales('daily', lookback=60)
forecast_data = {d: v for d, v in daily_series}
print(f"   Total entries from aggregate_sales: {len(daily_series)}")

# Get data from sales_dashboard method
print("\n2. Sales Dashboard Data:")
try:
    sales_for_days = Sale.objects.filter(date__gte=start_date).values('date', 'revenue')
    day_map = {}
    for rec in sales_for_days:
        d = rec.get('date')
        if d is None:
            continue
        if hasattr(d, 'date'):
            d = d.date()
        entry = day_map.setdefault(d, {'revenue': 0.0, 'orders': 0})
        entry['revenue'] += float(rec.get('revenue') or 0)
        entry['orders'] += 1
    
    dashboard_data = {d: data['revenue'] for d, data in day_map.items()}
    print(f"   Total entries from sales_dashboard: {len(dashboard_data)}")
except Exception as e:
    print(f"   ERROR: {e}")
    dashboard_data = {}

# Compare
print("\n3. Comparison:")
print(f"   {'Date':<12} {'Forecast':<15} {'Dashboard':<15} {'Match':<10}")
print("   " + "-" * 52)

all_dates = set(list(dashboard_data.keys()))
all_dates.update([d for d in [date.fromisoformat(d) for d in forecast_data.keys()]])

mismatches = 0
for d in sorted(all_dates):
    d_iso = d.isoformat()
    forecast_val = forecast_data.get(d_iso, 0)
    dashboard_val = dashboard_data.get(d, 0)
    match = "✓" if abs(forecast_val - dashboard_val) < 0.01 else "✗ MISMATCH"
    if match == "✗ MISMATCH":
        mismatches += 1
    print(f"   {d_iso:<12} {forecast_val:<15.2f} {dashboard_val:<15.2f} {match:<10}")

print("\n" + "=" * 80)
if mismatches == 0:
    print("✓ SUCCESS: Historical data matches between forecast and dashboard!")
else:
    print(f"✗ FAILURE: Found {mismatches} mismatches in historical data.")
print("=" * 80)
