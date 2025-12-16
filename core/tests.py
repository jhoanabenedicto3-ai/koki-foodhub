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
    def test_forecast_view_renders_for_admin(self):
        # Create an admin user and ensure the forecast page renders
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        from django.contrib.auth.models import Group
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)
        resp = c.get('/forecast/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sales Forecast', resp.content.decode('utf-8'))

    def test_forecast_api_permissions_and_payload(self):
        from django.contrib.auth.models import User, Group
        anon = self.client
        resp = anon.get('/forecast/api/')
        # unauthenticated clients should be redirected to login
        self.assertNotEqual(resp.status_code, 200)

        # create admin and test access
        admin = User.objects.create_superuser('admin2', 'a2@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)
        resp = c.get('/forecast/api/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('daily', data)
        self.assertIn('weekly', data)
        self.assertIn('monthly', data)
        # validate structure
        self.assertIsInstance(data['daily']['labels'], list)
        self.assertIsInstance(data['daily']['actual'], list)
