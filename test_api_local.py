#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth import get_user_model
from core.views import forecast_data_api
from django.test import RequestFactory

User = get_user_model()
user = User.objects.filter(is_superuser=True).first() or User.objects.create_superuser('admin', 'admin@test.com', 'testpass')

rf = RequestFactory()
req = rf.get('/forecast/api/')
req.user = user

resp = forecast_data_api(req)
content = resp.content.decode()

print(f"Response status: {resp.status_code}")
print(f"Response length: {len(content)}")

if 'daily_revenue' in content:
    print("✓ daily_revenue in API response")
else:
    print("✗ daily_revenue NOT in API response")

print("\nFirst 2000 chars:")
print(content[:2000])
