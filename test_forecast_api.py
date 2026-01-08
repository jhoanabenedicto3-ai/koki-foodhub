#!/usr/bin/env python
"""Test the forecast API to verify it's returning proper forecast data."""
import os
import django
import sys
from datetime import datetime, timedelta

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')

# Don't fail on DATABASE_URL check during local testing
try:
    django.setup()
except Exception as e:
    print(f"Warning: Django setup issue: {e}")
    print("Continuing anyway...")

# Now try to test
try:
    from core.services.forecasting import forecast_time_series, aggregate_sales
    
    # Get some sample data
    print("=" * 60)
    print("Testing forecast_time_series function")
    print("=" * 60)
    
    # Test 1: Empty series
    print("\nTest 1: Empty series")
    result = forecast_time_series([], horizon=30)
    print(f"  Result: {result}")
    print(f"  Forecast count: {len(result.get('forecast', []))}")
    
    # Test 2: Single value
    print("\nTest 2: Single value")
    result = forecast_time_series([('2025-01-01', 100)], horizon=30)
    print(f"  Result: {result}")
    print(f"  Forecast count: {len(result.get('forecast', []))}")
    print(f"  First 5 forecast values: {result.get('forecast', [])[:5]}")
    
    # Test 3: Small series (7 days)
    print("\nTest 3: Small series (7 days)")
    small_series = [
        (f'2025-01-{(i+1):02d}', 100 + i*10) 
        for i in range(7)
    ]
    result = forecast_time_series(small_series, horizon=30)
    print(f"  Input: {len(small_series)} points")
    print(f"  Result: {result}")
    print(f"  Forecast count: {len(result.get('forecast', []))}")
    print(f"  First 5 forecast values: {result.get('forecast', [])[:5]}")
    
    # Test 4: Larger series
    print("\nTest 4: Larger series (30 days)")
    large_series = [
        (f'2024-12-{((i % 31) + 1):02d}', 100 + i*5) 
        for i in range(30)
    ]
    result = forecast_time_series(large_series, horizon=30)
    print(f"  Input: {len(large_series)} points")
    print(f"  Result keys: {result.keys()}")
    print(f"  Forecast count: {len(result.get('forecast', []))}")
    print(f"  First 5 forecast values: {result.get('forecast', [])[:5]}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
    print(f"  Accuracy: {result.get('accuracy', 'N/A')}")
    
except Exception as e:
    import traceback
    print(f"Error during testing: {e}")
    traceback.print_exc()
