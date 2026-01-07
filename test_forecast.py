#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
os.environ['DEBUG'] = 'True'
os.environ['USE_DOTENV'] = 'true'

django.setup()

from core.services.forecasting import aggregate_sales, forecast_time_series
import json

try:
    print("Testing aggregate_sales...")
    daily = aggregate_sales('daily', lookback=60)
    print(f"Daily data: {len(daily)} items")
    if daily:
        print(f"  First: {daily[0]}")
        print(f"  Last: {daily[-1]}")
    
    print("\nTesting forecast_time_series...")
    forecast = forecast_time_series(daily, horizon=30)
    print(f"Forecast keys: {forecast.keys()}")
    print(f"Forecast type check:")
    for key, val in forecast.items():
        print(f"  {key}: {type(val)} = {val}")
    
    print("\nTesting JSON serialization...")
    test_json = json.dumps({
        'labels': [d for d, _ in daily],
        'actual': [v for _, v in daily],
        'forecast': forecast.get('forecast', []),
        'upper': forecast.get('upper', []),
        'lower': forecast.get('lower', []),
        'confidence': forecast.get('confidence', 0)
    })
    print(f"JSON serialization OK: {len(test_json)} characters")
    
except Exception as e:
    import traceback
    print(f"Error: {e}")
    traceback.print_exc()
