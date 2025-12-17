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

    def test_forecast_view_handles_missing_moving_average(self):
        """If the forecasting helper 'moving_average_forecast' is missing, the view should still render (no 500)."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_missing', 'am@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Temporarily remove the helper from the forecasting module to simulate a partial import failure
        import importlib
        mod = importlib.import_module('core.services.forecasting')
        had = hasattr(mod, 'moving_average_forecast')
        saved = getattr(mod, 'moving_average_forecast', None)
        if had:
            delattr(mod, 'moving_average_forecast')
        try:
            resp = c.get('/forecast/')
            # Should still render a friendly page instead of 500
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sales Forecast', resp.content.decode('utf-8'))
        finally:
            # restore the helper if it existed
            if had:
                setattr(mod, 'moving_average_forecast', saved)

    def test_forecast_view_handles_missing_forecast_time_series(self):
        """If the forecasting helper 'forecast_time_series' is missing, the view should still render (no 500)."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_missing2', 'am2@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Temporarily remove the helper from the forecasting module to simulate a partial import failure
        import importlib
        mod = importlib.import_module('core.services.forecasting')
        had = hasattr(mod, 'forecast_time_series')
        saved = getattr(mod, 'forecast_time_series', None)
        if had:
            delattr(mod, 'forecast_time_series')
        try:
            resp = c.get('/forecast/')
            # Should still render a friendly page instead of 500
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sales Forecast', resp.content.decode('utf-8'))
        finally:
            # restore the helper if it existed
            if had:
                setattr(mod, 'forecast_time_series', saved)

    def test_forecast_api_returns_error_id_on_unexpected_exception(self):
        """When the API encounters an unexpected exception it should return a JSON error with an id for lookup."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_err', 'ae@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        import importlib
        mod = importlib.import_module('core.services.forecasting')
        # Temporarily replace forecast_time_series to force an exception during API processing
        saved = getattr(mod, 'forecast_time_series', None)
        def boom(*a, **k):
            raise Exception('boom!')
        setattr(mod, 'forecast_time_series', boom)
        try:
            resp = c.get('/forecast/api/')
            self.assertEqual(resp.status_code, 500)
            data = resp.json()
            self.assertIn('error', data)
            self.assertIn('id', data)
            self.assertTrue(len(data['id']) > 0)
        finally:
            if saved is not None:
                setattr(mod, 'forecast_time_series', saved)

    def test_forecast_exception_middleware_returns_id(self):
        """The middleware should catch uncaught exceptions and return an error id."""
        from django.test.client import RequestFactory
        from django.contrib.auth.models import User, Group
        from core.middleware.forecast_exceptions import ForecastExceptionMiddleware

        # Create an admin user
        admin = User.objects.create_superuser('admin_mw', 'amw@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)

        # Create a get_response that raises an exception to simulate an unhandled error
        def raising_get_response(req):
            raise RuntimeError('boom-mw')

        mw = ForecastExceptionMiddleware(raising_get_response)
        rf = RequestFactory()
        req = rf.get('/forecast/api/')
        req.user = admin
        # header to mimic fetch XHR
        req.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        resp = mw(req)
        self.assertEqual(resp.status_code, 500)
        import json
        data = json.loads(resp.content)
        self.assertIn('error', data)
        self.assertIn('id', data)
        self.assertTrue(len(data['id']) > 0)

    def test_aggregate_sales_caps_per_sale(self):
        """Ensure extremely large per-sale unit counts are capped when aggregating."""
        from .services.forecasting import aggregate_sales
        from datetime import date

        # Choose a fixed week start so we can find the weekly label
        week_start = date(2025, 11, 24)

        # Create a product for these test sales
        p = Product.objects.create(name="Test Cap", category="Test", price=Decimal("10.00"))

        # Add one huge sale and one small sale in the same week
        Sale.objects.create(product=p, date=week_start, units_sold=3000, revenue=Decimal('3000.00'))
        Sale.objects.create(product=p, date=week_start, units_sold=14, revenue=Decimal('140.00'))

        series = aggregate_sales('weekly', lookback=12)
        # find the entry for our week
        label_to_find = week_start.isoformat()
        matching = [s for s in series if s[0] == label_to_find]
        self.assertTrue(matching, f"Weekly label {label_to_find} not found in series")
        total = matching[0][1]

        # The per-sale cap in production code is 100 units per sale; expected total is min(3000,100) + 14 = 114
        self.assertEqual(total, 114)
