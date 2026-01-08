"""
Django management command to populate test sales data for the last 7 days.
Useful for demo/testing purposes on fresh deployments.
"""
from django.core.management.base import BaseCommand
from core.models import Product, Sale
from django.utils import timezone
from datetime import timedelta
import random


class Command(BaseCommand):
    help = 'Create test sales data for fries and carbonara for the last 7 days'

    def handle(self, *args, **options):
        # Get the products
        try:
            fries = Product.objects.get(name='fries')
            carbonara = Product.objects.get(name='carbonara')
        except Product.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Products "fries" and "carbonara" not found in database')
            )
            return

        today = timezone.now().date()
        created_count = 0

        # Create sales for the last 7 days
        for days_back in range(7):
            sale_date = today - timedelta(days=days_back)

            # Fries: random 1-5 units per day
            fries_units = random.randint(1, 5)
            fries_price = float(fries.price or 100)
            Sale.objects.get_or_create(
                product=fries,
                date=sale_date,
                defaults={
                    'units_sold': fries_units,
                    'revenue': fries_units * fries_price,
                }
            )
            created_count += 1

            # Carbonara: random 1-5 units per day
            carbonara_units = random.randint(1, 5)
            carbonara_price = float(carbonara.price or 150)
            Sale.objects.get_or_create(
                product=carbonara,
                date=sale_date,
                defaults={
                    'units_sold': carbonara_units,
                    'revenue': carbonara_units * carbonara_price,
                }
            )
            created_count += 1

        # Verify creation
        fries_recent = Sale.objects.filter(
            product=fries,
            date__gte=today - timedelta(days=7)
        ).count()
        carbonara_recent = Sale.objects.filter(
            product=carbonara,
            date__gte=today - timedelta(days=7)
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Created {created_count} sales records for the past 7 days\n'
                f'   Fries: {fries_recent} sales\n'
                f'   Carbonara: {carbonara_recent} sales'
            )
        )
