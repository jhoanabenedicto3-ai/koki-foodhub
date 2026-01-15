from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from core.models import Product, Sale
import random

class Command(BaseCommand):
    help = 'Populate sales data for product forecasting'

    def handle(self, *args, **options):
        self.stdout.write('Populating sales data...')
        
        # Get all active products
        products = Product.objects.filter(is_active=True)
        
        if not products.exists():
            self.stdout.write(self.style.ERROR('No active products found'))
            return
        
        # Clear existing sales (optional - comment out if you want to keep existing data)
        # Sale.objects.all().delete()
        
        # Generate sales data for the last 30 days
        now = timezone.now()
        sales_created = 0
        
        for day_offset in range(30):
            date = now - timedelta(days=day_offset)
            
            # Generate 5-15 sales per day
            num_sales = random.randint(5, 15)
            
            for _ in range(num_sales):
                # Pick a random product
                product = random.choice(products)
                
                # Random quantity (1-5 units per sale)
                quantity = random.randint(1, 5)
                
                # Create sale
                Sale.objects.create(
                    product=product,
                    quantity=quantity,
                    sale_price=float(product.price),
                    created_at=date - timedelta(hours=random.randint(0, 23), minutes=random.randint(0, 59))
                )
                sales_created += 1
        
        self.stdout.write(self.style.SUCCESS(f'Successfully created {sales_created} sales records'))
        
        # Print summary
        total_sales = Sale.objects.count()
        products_with_sales = Product.objects.filter(sale__isnull=False).distinct().count()
        
        self.stdout.write(f'Total sales in database: {total_sales}')
        self.stdout.write(f'Products with sales: {products_with_sales}')
