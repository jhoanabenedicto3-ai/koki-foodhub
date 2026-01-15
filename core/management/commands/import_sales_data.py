#!/usr/bin/env python
"""
Django management command to import sales data on Render deployment
Usage: python manage.py import_sales_data
"""
import os
import json
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from core.models import Sale, Product


class Command(BaseCommand):
    help = 'Import recent sales data from render_recent_sales.json'

    def handle(self, *args, **options):
        json_file = 'render_recent_sales.json'
        
        if not os.path.exists(json_file):
            self.stdout.write(self.style.WARNING(f'{json_file} not found, skipping import'))
            return
        
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        sales_data = data.get('sales', [])
        created = 0
        skipped = 0
        
        for sale_data in sales_data:
            try:
                product = Product.objects.get(name=sale_data['product_name'])
                
                # Check if this sale already exists to avoid duplicates
                date = sale_data['date']
                existing = Sale.objects.filter(
                    product=product,
                    date=date,
                    units_sold=sale_data['units_sold']
                ).exists()
                
                if not existing:
                    Sale.objects.create(
                        product=product,
                        date=date,
                        timestamp=timezone.now(),
                        units_sold=sale_data['units_sold'],
                        revenue=Decimal(sale_data['revenue'])
                    )
                    created += 1
                else:
                    skipped += 1
            except Product.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Product not found: {sale_data['product_name']}"))
                skipped += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error importing sale: {e}"))
                skipped += 1
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported {created} sales, skipped {skipped}'))
