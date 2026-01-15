#!/usr/bin/env python
"""
Export recent sales data to JSON for Render deployment
"""
import os
from dotenv import load_dotenv
load_dotenv()
os.environ['DEBUG'] = 'True'

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Sale, Product
from django.utils import timezone
from datetime import timedelta
import json
from decimal import Decimal

# Get sales from last 30 days
today = timezone.localdate()
thirty_days_ago = today - timedelta(days=30)

sales = Sale.objects.filter(date__gte=thirty_days_ago).select_related('product')

data = {
    'sales': []
}

for sale in sales:
    data['sales'].append({
        'product_name': sale.product.name,
        'date': str(sale.date),
        'units_sold': sale.units_sold,
        'revenue': str(sale.revenue)
    })

# Save to JSON
output_file = 'render_recent_sales.json'
with open(output_file, 'w') as f:
    json.dump(data, f, indent=2)

print(f"✓ Exported {len(data['sales'])} sales records to {output_file}")
