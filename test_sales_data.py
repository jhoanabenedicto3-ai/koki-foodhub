import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Sale, Product
from django.utils import timezone
from django.db.models import Sum
from datetime import timedelta

today = timezone.localtime().date()
week_ago = today - timedelta(days=6)
month_ago = today - timedelta(days=29)

# Check total sales data
total_sales = Sale.objects.count()
print(f'Total sales records: {total_sales}')

# Check sales date range
first_sale = Sale.objects.order_by('date').first()
last_sale = Sale.objects.order_by('-date').first()
print(f'Sales date range: {first_sale.date if first_sale else None} to {last_sale.date if last_sale else None}')

# Check last 7 days
last_7_count = Sale.objects.filter(date__gte=week_ago, date__lte=today).count()
print(f'Sales records in last 7 days: {last_7_count}')

# Sample a product
products_with_sales = Product.objects.filter(sales__isnull=False).distinct().count()
print(f'Products with sales: {products_with_sales}')

# Show sample product data
sample = Product.objects.filter(sales__isnull=False).first()
if sample:
    print(f'\nSample product: {sample.name} ({sample.category})')
    last_7_sales = sample.sales.filter(date__gte=week_ago, date__lte=today).aggregate(total=Sum('units_sold'))
    last_30_sales = sample.sales.filter(date__gte=month_ago, date__lte=today).aggregate(total=Sum('units_sold'))
    print(f'  Last 7 days units: {last_7_sales["total"] or 0}')
    print(f'  Last 30 days units: {last_30_sales["total"] or 0}')

# Show top 5 products by recent sales
print('\nTop 5 products by last 7 days sales:')
top_products = []
for p in Product.objects.all()[:20]:
    last_7 = p.sales.filter(date__gte=week_ago, date__lte=today).aggregate(total=Sum('units_sold'))['total'] or 0
    if last_7 > 0:
        top_products.append((p.name, last_7))

top_products.sort(key=lambda x: x[1], reverse=True)
for name, units in top_products[:5]:
    print(f'  {name}: {units} units')
