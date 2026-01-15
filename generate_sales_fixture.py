#!/usr/bin/env python
"""
Generate Django fixture with sample sales data for the Product Performance table
"""
import os
from dotenv import load_dotenv
load_dotenv()
os.environ['DEBUG'] = 'True'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Sale, Product
from django.core import serializers
from django.utils import timezone
from datetime import timedelta
import io

# Get all sales from last 30 days
today = timezone.localdate()
thirty_days_ago = today - timedelta(days=30)

sales = Sale.objects.filter(date__gte=thirty_days_ago).order_by('id')

# Serialize to JSON fixture format
out = io.StringIO()
serializers.serialize('json', sales, stream=out, indent=2)
fixture_json = out.getvalue()

# Save as fixture
with open('core/fixtures/recent_sales.json', 'w') as f:
    f.write(fixture_json)

print(f"✓ Generated fixture with {sales.count()} sales records")
print(f"  File: core/fixtures/recent_sales.json")
