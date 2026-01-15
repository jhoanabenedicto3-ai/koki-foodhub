#!/usr/bin/env python
"""
Generate realistic historical sales data for the last 90 days
to populate the forecast dashboard with realistic predictions.
"""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
os.environ['DEBUG'] = 'True'

import django
django.setup()

from core.models import Sale, Product
from datetime import timedelta
from django.utils import timezone
import random

# Get current date
end_date = timezone.localdate()
start_date = end_date - timedelta(days=90)

print("Generating sales data from", start_date, "to", end_date)

# Get all active products
products = Product.objects.filter(is_active=True)
print(f"Processing {products.count()} products")

# Sales patterns by product category (average daily sales)
category_patterns = {
    'Burgers': {'base': 150, 'variance': 50},
    'Pizza': {'base': 130, 'variance': 45},
    'Appetizers': {'base': 100, 'variance': 30},
    'Sides': {'base': 90, 'variance': 25},
    'Salads': {'base': 80, 'variance': 20},
    'Beverages': {'base': 200, 'variance': 60},
    'Dessert': {'base': 70, 'variance': 20},
}

# Iterate through each day
current_date = start_date
sales_created = 0

while current_date <= end_date:
    # For each product, potentially create a sale
    for product in products:
        category = product.category or 'Other'
        pattern = category_patterns.get(category, {'base': 100, 'variance': 30})
        
        # Generate sales for this product on this day with some probability
        # Higher chance on weekdays, lower on weekends
        day_of_week = current_date.weekday()
        is_weekend = day_of_week >= 5
        
        base_units = pattern['base']
        if is_weekend:
            base_units = int(base_units * 0.8)  # 20% less on weekends
        
        # Add randomness
        variance = pattern['variance']
        units = max(0, base_units + random.randint(-variance, variance))
        
        # Maybe skip some days for variety
        if random.random() > 0.7:
            units = 0
        
        # If we have units for this product on this day
        if units > 0:
            # Check if sale already exists
            existing = Sale.objects.filter(
                product=product,
                date=current_date
            ).exists()
            
            if not existing:
                sale = Sale.objects.create(
                    product=product,
                    date=current_date,
                    units_sold=units,
                    revenue=units * float(product.price or 10)
                )
                sales_created += 1
    
    current_date += timedelta(days=1)

print(f"Created {sales_created} new sales records")

# Verify data
from django.db.models import Sum
total_units = Sale.objects.filter(date__gte=start_date).aggregate(total=Sum('units_sold'))['total'] or 0
print(f"Total units sold in range: {total_units}")

# Show top products
from django.db.models import Count
top_products = Sale.objects.filter(date__gte=start_date).values('product__name').annotate(total=Sum('units_sold')).order_by('-total')[:5]
print("\nTop 5 products in this period:")
for item in top_products:
    print(f"  - {item['product__name']}: {item['total']} units")
