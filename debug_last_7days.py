import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.utils import timezone
from core.models import Sale
from datetime import timedelta
from django.db.models import Sum

today = timezone.localdate()
print(f"Today's date (app timezone): {today}")

week_ago = today - timedelta(days=6)
month_ago = today - timedelta(days=29)

print(f"Week ago: {week_ago}")
print(f"Month ago: {month_ago}")

# Check all sales
all_sales = Sale.objects.all().count()
print(f"\nTotal sales in DB: {all_sales}")

# Check sales by date in last 30 days
print("\nSales by date (last 30 days):")
sales_30 = Sale.objects.filter(date__gte=month_ago).values('date').annotate(count=Sum('units_sold')).order_by('-date')
for s in sales_30:
    print(f"  {s['date']}: {s['count']} units")

# Check for fries specifically
print("\nFries sales (last 30 days):")
fries_sales = Sale.objects.filter(product__name='fries', date__gte=month_ago).values('date').annotate(count=Sum('units_sold')).order_by('-date')
for s in fries_sales:
    print(f"  {s['date']}: {s['count']} units")

# Direct query test for last 7 days
fries_7 = Sale.objects.filter(product__name='fries', date__gte=week_ago, date__lte=today).aggregate(total=Sum('units_sold'))
print(f"\nFries last 7 days (direct query): {fries_7.get('total') or 0}")

# Direct query for last 30 days
fries_30 = Sale.objects.filter(product__name='fries', date__gte=month_ago, date__lte=today).aggregate(total=Sum('units_sold'))
print(f"Fries last 30 days (direct query): {fries_30.get('total') or 0}")
