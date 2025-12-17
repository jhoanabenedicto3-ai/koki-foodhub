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
        # CSV is present in repo and we aggregate last 100 rows -> expect non-empty daily series
        self.assertTrue(len(data['daily']['labels']) > 0)
        # API should indicate the data source
        self.assertIn('data_source', data)
        self.assertIn(data['data_source'], ('csv','db','unknown'))
        # New: summary and AI insights present
        self.assertIn('summary', data)
        self.assertIn('daily', data['summary'])
        self.assertIn('weekly', data['summary'])
        self.assertIn('monthly', data['summary'])
        self.assertIn('ai_insights', data)
        self.assertIsInstance(data['ai_insights'], list)

    def test_forecast_api_filters(self):
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin3', 'a3@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)
        # Use start date equal to today so daily series should include today's label if present
        from datetime import date
        today = date.today().isoformat()
        resp = c.get(f'/forecast/api/?start={today}')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('daily', data)

    def test_forecast_diag_endpoint(self):
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin4', 'a4@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)
        resp = c.get('/forecast/diag/')
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('data_source', data)
        self.assertIn(data['data_source'], ('csv','db','unknown'))
        self.assertIn('daily', data)
        self.assertIn('weekly', data)
        self.assertIn('monthly', data)

    def test_forecast_today_sales_matches_sales_page(self):
        """Forecast page should display today's revenue (currency) matching DB aggregates."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_today', 'today@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Ensure we have at least one sale for today from setUp
        from django.db.models import Sum
        from django.utils import timezone
        today = timezone.localdate()
        expected = float(Sale.objects.filter(date=today).aggregate(total=Sum('revenue')).get('total') or 0.0)

        resp = c.get('/forecast/')
        self.assertEqual(resp.status_code, 200)
        # Response context should include the numeric 'today_sales' matching revenue
        ctx = resp.context
        self.assertIn('today_sales', ctx)
        self.assertAlmostEqual(float(ctx['today_sales']), expected, places=2)
        # Ensure units are not displayed in the hero tiles (visual requirement)
        content = resp.content.decode('utf-8')
        self.assertNotIn('units /', content)
        # Parse JSON blob embedded in template to ensure daily series has today's label and value
        import json
        daily_json = json.loads(resp.context['daily_json'])
        labels = daily_json.get('labels', [])
        actual = daily_json.get('actual', [])
        from django.utils import timezone
        today = timezone.localdate().isoformat()
        if labels:
            self.assertEqual(labels[-1], today)
            # Check last actual equals DB aggregate for today's units
            expected_units = int(Sale.objects.filter(date=today).aggregate(total=Sum('units_sold')).get('total') or 0)
            self.assertEqual(int(actual[-1]), expected_units)
