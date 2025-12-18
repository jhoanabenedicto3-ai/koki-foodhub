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

    def test_forecast_view_renders_for_authenticated_user(self):
        """Ensure a regular authenticated user can load the forecast page."""
        from django.contrib.auth.models import User, Group
        user = User.objects.create_user('user1', 'u1@example.com', 'pass')
        c = self.client
        c.force_login(user)
        resp = c.get('/forecast/')
        # Regular users are allowed to view the page (redirecting to login would be wrong)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Sales Forecast', resp.content.decode('utf-8'))

    def test_forecast_api_permissions_and_payload(self):
        from django.contrib.auth.models import User, Group
        anon = self.client
        resp = anon.get('/forecast/api/')
        # unauthenticated clients should be redirected to login
        self.assertNotEqual(resp.status_code, 200)

        # create a regular authenticated user and test access (the API should be available to logged-in users)
        user = User.objects.create_user('user_api', 'uapi@example.com', 'pass')
        c = self.client
        c.force_login(user)
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

    def test_forecast_view_handles_missing_numeric_libs(self):
        """If numpy/pandas/sklearn are unavailable the forecast page should still render (no 500)."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_missing_libs', 'aml@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        import importlib, builtins
        real_import = builtins.__import__

        def broken_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith('numpy') or name.startswith('sklearn') or name.startswith('pandas'):
                raise ImportError('simulated missing dependency')
            return real_import(name, globals, locals, fromlist, level)

        try:
            # Patch import to simulate missing libs and reload the forecasting module
            builtins.__import__ = broken_import
            mod = importlib.import_module('core.services.forecasting')
            importlib.reload(mod)

            resp = c.get('/forecast/')
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Sales Forecast', resp.content.decode('utf-8'))
        finally:
            builtins.__import__ = real_import
            # Reload module to restore original behavior
            try:
                importlib.reload(importlib.import_module('core.services.forecasting'))
            except Exception:
                pass

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

    def test_moving_average_forecast_uses_historical_values(self):
        """Ensure the simple moving-average forecast reflects recent history (not a fixed cap)."""
        from .services.forecasting import moving_average_forecast
        # Create a product and attach some small unit sales
        p = Product.objects.create(name="Test Item", category="Test", price=Decimal("50.00"))
        from datetime import date, timedelta
        today = date.today()
        # Sales with small values (should not be rounded up to 100)
        Sale.objects.create(product=p, date=today - timedelta(days=2), units_sold=2, revenue=Decimal("100.00"))
        Sale.objects.create(product=p, date=today - timedelta(days=1), units_sold=3, revenue=Decimal("150.00"))
        Sale.objects.create(product=p, date=today, units_sold=4, revenue=Decimal("200.00"))

        res = moving_average_forecast(window=3, lookback_days=7)
        dbf = res.get('db_forecasts', {})
        self.assertIn(p.id, dbf)
        pred = dbf[p.id].get('forecast', None)
        # Forecast should be roughly the recent average (2-4 => ~3) and must NOT be 100
        self.assertIsNotNone(pred)
        self.assertNotEqual(pred, 100)
        self.assertTrue(1 <= pred <= 10, f'Unexpected forecast {pred}')

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

    def test_forecast_prefers_db_when_db_has_recent_data(self):
        """Ensure that when the DB has recent meaningful data, the view uses DB series for forecasting (not stale CSV)."""
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_pref', 'ap@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Request the forecast page and inspect context
        resp = c.get('/forecast/?debug=1')
        self.assertEqual(resp.status_code, 200)
        ctx = resp.context
        # Our test DB seeded in setUp contains non-zero last-week units; the view should therefore prefer DB
        self.assertEqual(ctx.get('data_source'), 'db')
        # weekly forecast payload should be generated from DB weekly series and not be a flat 100 series
        weekly_json = ctx.get('weekly_json')
        import json
        weekly = json.loads(weekly_json)
        self.assertFalse(all(v == 100 for v in weekly.get('forecast', [])), 'Weekly forecast should not be a flat 100 from stale CSV')

    def test_stale_csv_is_ignored(self):
        """If the CSV has only very old data, the view should ignore it and prefer DB series (or show no data) to avoid flat 100 forecasts."""
        from django.contrib.auth.models import User, Group
        import importlib
        admin = User.objects.create_superuser('admin_stale', 'astale@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Monkeypatch csv_aggregate_series to return a single very old row
        # Even if the CSV helper returns stale values, the forecast view must rely on DB-only data
        mod = importlib.import_module('core.services.csv_forecasting')
        saved = getattr(mod, 'csv_aggregate_series', None)
        def stale_csv(limit=100):
            return {'daily': [('2015-12-31', 100)], 'weekly': [('2015-12-28', 100)], 'monthly': [('2015-12', 100)]}
        setattr(mod, 'csv_aggregate_series', stale_csv)
        try:
            resp = c.get('/forecast/?debug=1')
            self.assertEqual(resp.status_code, 200)
            ctx = resp.context
            # CSV is irrelevant -> view must still report DB as source
            self.assertEqual(ctx.get('data_source'), 'db')
            import json
            weekly = json.loads(ctx.get('weekly_json'))
            # Weekly forecast should not be flat 100 repeated
            self.assertFalse(all(v == 100 for v in weekly.get('forecast', [])))
        finally:
            if saved is not None:
                setattr(mod, 'csv_aggregate_series', saved)

    def test_forecast_ignores_csv_errors(self):
        """Ensure that CSV-related errors (or the presence of CSV helpers) do not affect DB-only forecasting."""
        import importlib
        from django.contrib.auth.models import User, Group
        admin = User.objects.create_superuser('admin_csverr', 'acsv@example.com', 'pass')
        grp, _ = Group.objects.get_or_create(name='Admin')
        admin.groups.add(grp)
        c = self.client
        c.force_login(admin)

        # Monkeypatch get_csv_forecast to raise if called; ensure forecast ignores CSV module errors
        mod = importlib.import_module('core.services.csv_forecasting')
        saved_get = getattr(mod, 'get_csv_forecast', None)
        def explode(*args, **kwargs):
            raise RuntimeError('CSV should not be called')
        setattr(mod, 'get_csv_forecast', explode)

        try:
            # View page should render and report DB as source
            resp = c.get('/forecast/?debug=1')
            self.assertEqual(resp.status_code, 200)
            ctx = resp.context
            self.assertEqual(ctx.get('data_source'), 'db')

            # API should also return data_source=db and status 200
            resp2 = c.get('/forecast/api/')
            self.assertEqual(resp2.status_code, 200)
            data = resp2.json()
            self.assertIn('data_source', data)
            self.assertEqual(data['data_source'], 'db')

            # Also assert that a per-product forecast influenced by a giant outlier
            # is clamped so the API doesn't return absurd values. Create a contrived
            # sale with an enormous units_sold and confirm moving_average_forecast caps it.
            from core.services.forecasting import moving_average_forecast
            large = Sale.objects.create(product=Product.objects.first(), units_sold=3000, revenue=3000.0, date='2025-11-30')
            prod = moving_average_forecast(window=3).get('db_forecasts', {})
            # Every forecast must be below or equal to our MAX_UNITS_PER_SALE after the cap
            from core.services.forecasting import MAX_UNITS_PER_SALE
            for p, r in prod.items():
                self.assertLessEqual(int(r.get('forecast', 0)), MAX_UNITS_PER_SALE)
        finally:
            if saved_get is not None:
                setattr(mod, 'get_csv_forecast', saved_get)

    def test_model_selection_prefers_non_ma_on_trend(self):
        """Model selection should prefer linear/holt over simple MA for trending data."""
        from core.services.forecasting import select_best_forecasting_method
        # create a trending series with small noise
        values = [10 + i * 2 + (1 if i % 7 == 0 else 0) for i in range(30)]
        method, params, diag = select_best_forecasting_method(values, horizon=7)
        self.assertIn(method, ('linear', 'holt'))
        # chosen model's MAPE should be no worse than MA
        scores = diag.get('scores', {})
        self.assertLessEqual(scores.get(method, float('inf')), scores.get('ma', float('inf')))

    def test_selection_works_if_numeric_libs_missing(self):
        """Even if numpy/sklearn/pandas are unavailable, selection should run and pick a model (holt or ma)."""
        import builtins, importlib
        real_import = builtins.__import__
        def broken_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name.startswith('numpy') or name.startswith('sklearn') or name.startswith('pandas'):
                raise ImportError('simulated missing dependency')
            return real_import(name, globals, locals, fromlist, level)

        try:
            builtins.__import__ = broken_import
            # reload module to exercise import-time behavior
            mod = importlib.import_module('core.services.forecasting')
            importlib.reload(mod)
            from core.services.forecasting import select_best_forecasting_method
            values = [50 + (i * 3) + ((-1) ** i) * 2 for i in range(25)]
            method, params, diag = select_best_forecasting_method(values, horizon=5)
            self.assertIn(method, ('holt', 'ma'))
        finally:
            builtins.__import__ = real_import
            try:
                importlib.reload(importlib.import_module('core.services.forecasting'))
            except Exception:
                pass
