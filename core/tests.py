from django.test import TestCase
from .models import Product, InventoryItem, Sale
from datetime import date, timedelta
from decimal import Decimal

class Seed(TestCase):
    def setUp(self):
        p = Product.objects.create(name="Chicken Bowl", category="Meals", price=Decimal("149.00"))
        InventoryItem.objects.create(product=p, sku="CKB-001", quantity=50, reorder_point=10)
        for i in range(6):
            units = 10 + i
            Sale.objects.create(product=p, date=date.today() - timedelta(days=i), units_sold=units, revenue=Decimal("149.00") * units)
