from datetime import date, timedelta
from collections import defaultdict
import os
import logging
from ..models import Sale, Product
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import relativedelta

# NOTE: numpy, pandas and scikit-learn are optional runtime dependencies used
# for CSV-based helpers and linear-regression forecasts. Importing them at
# module import time caused some deployed instances to raise ImportError and
# produce a Server Error (500) when those packages weren't available. To be
# resilient we import heavy numeric libs only inside the functions that need
# them and provide safe fallbacks when they're missing.
logger = logging.getLogger(__name__)

# Cap per-sale units so single bad rows don't dominate forecasts
MAX_UNITS_PER_SALE = 100

def load_csv_data(csv_path=None):
    """Load sales data from CSV file"""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), '../../pizzaplace.csv')
    
    if not os.path.exists(csv_path):
        return None
    
    try:
        # Import pandas only when CSV helpers are invoked
        import pandas as pd
    except Exception as exc:  # pragma: no cover - environment-dependent
        logger.exception('Pandas unavailable; CSV helpers disabled: %s', exc)
        return None

    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        logger.exception('Error loading CSV: %s', e)
        return None


def csv_aggregate_series(limit=100):
    """Return aggregated series (daily, weekly, monthly) computed from the CSV.
    Limit to the most recent `limit` rows in the CSV to keep processing bounded.
    Returns dict with keys 'daily', 'weekly', 'monthly' where each value is a list of
    (label, units) tuples ordered chronologically (oldest -> newest).
    """
    df = load_csv_data()
    if df is None or df.empty:
        return {'daily': [], 'weekly': [], 'monthly': []}

    # Ensure date column is datetime and sort by date
    df = df.sort_values('date')

    # Limit to `limit` most recent rows
    if limit is not None:
        df = df.tail(limit)

    # DAILY: count rows per date
    daily = df.groupby(df['date'].dt.date).size().reset_index(name='units')
    # Fill missing days between min and max date with zeros for nicer charts
    min_d = daily['date'].min()
    max_d = daily['date'].max()
    all_dates = pd.date_range(start=min_d, end=max_d, freq='D')
    daily = daily.set_index('date').reindex(all_dates, fill_value=0).rename_axis('date').reset_index()
    daily_series = [(row['date'].date().isoformat(), int(row['units'])) for _, row in daily.iterrows()]

    # WEEKLY: group by week starting Monday
    df_week = df.copy()
    df_week['week_start'] = df_week['date'].dt.to_period('W').apply(lambda r: r.start_time.date())
    weekly = df_week.groupby('week_start').size().reset_index(name='units')
    weekly_series = [(row['week_start'].isoformat(), int(row['units'])) for _, row in weekly.iterrows()]

    # MONTHLY: group by year-month
    df_month = df.copy()
    df_month['month'] = df_month['date'].dt.to_period('M').apply(lambda r: r.start_time.date())
    monthly = df_month.groupby('month').size().reset_index(name='units')
    monthly_series = [(row['month'].strftime('%Y-%m'), int(row['units'])) for _, row in monthly.iterrows()]

    return {'daily': daily_series, 'weekly': weekly_series, 'monthly': monthly_series}

def get_csv_forecast(csv_path=None, limit=100):
    """
    Train ML model on CSV data and return forecasts for each product.

    By default this function limits processing to the most recent 100 rows of the CSV
    (to keep production CPU/memory bounded). Pass a different `limit` to override.

    Returns dict: product_name -> { 'forecast': units, 'trend': str, 'confidence': float, 'history': [...] }
    """
    df = load_csv_data(csv_path)
    if df is None:
        return {}
    # Limit to most recent `limit` rows to keep processing bounded
    if limit is not None:
        try:
            df = df.sort_values('date').tail(limit)
        except Exception:
            pass
    
    results = {}
    
    # Group by product name
    # Try to import numeric libs lazily; if they're not present return empty results
    try:
        import numpy as np
        from sklearn.linear_model import LinearRegression
    except Exception as exc:  # pragma: no cover - only triggers when libs absent
        logger.exception('Numeric libs unavailable for CSV forecasting: %s', exc)
        return {}

    for product_name, group in df.groupby('name'):
        # Count units sold per day
        daily_sales = group.groupby('date').size().reset_index(name='units')
        
        if len(daily_sales) < 3:
            continue
        
        # Prepare training data
        X = np.arange(len(daily_sales)).reshape(-1, 1)
        y = daily_sales['units'].values

        # Train linear regression model
        model = LinearRegression()
        model.fit(X, y)

        # Get forecast for next day
        next_day = np.array([[len(daily_sales)]])
        forecast = max(1, int(model.predict(next_day)[0]))
        
        # Calculate trend
        slope = model.coef_[0]
        if slope > 0.5:
            trend = "increasing"
        elif slope < -0.5:
            trend = "decreasing"
        else:
            trend = "stable"
        
        # Calculate confidence (R² score as percentage, with minimum threshold)
        r_squared = model.score(X, y)
        
        # Convert R² to percentage (0-100)
        # If R² is negative, it means the model is worse than a simple mean, so set to 0
        if r_squared < 0:
            confidence = 0.0
        else:
            confidence = round(r_squared * 100, 2)
        
        # Ensure confidence is never 0 if we have some data (minimum 10% if model performs reasonably)
        if confidence == 0 and len(daily_sales) >= 3:
            # Calculate consistency score based on variance
            variance = float(y.var())
            mean = float(y.mean())
            if mean > 0:
                coefficient_of_variation = variance / (mean ** 2)
                # Lower CV means more consistent = higher confidence
                consistency_score = max(10.0, 100.0 - (coefficient_of_variation * 50))
                confidence = min(85.0, consistency_score)
            else:
                confidence = 10.0
        
        # Get recent history
        history = daily_sales.tail(7).values.tolist()
        # Derive accuracy label
        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        results[product_name] = {
            'forecast': forecast,
            'trend': trend,
            'confidence': confidence,
            'accuracy': accuracy,
            'history': history,
            'avg': float(y.mean()),
            'last_7_days': int(y[-7:].sum())
        }
    
    return results

def moving_average_forecast(window=3, lookback_days=21):
    """
    Returns dict: product_id -> { 'history': [(date, units)], 'forecast': int, 'avg': float }
    Simple moving average over last `window` sales entries within `lookback_days`.
    Outlier protection: cap per-sale units at `MAX_UNITS_PER_SALE` before averaging so a
    single large sale doesn't dominate the forecast.
    """
    start = date.today() - timedelta(days=lookback_days)
    sales = Sale.objects.filter(date__gte=start).order_by("product_id", "date")
    series = defaultdict(list)

    for s in sales:
        series[s.product_id].append((s.date, s.units_sold))

    results = {}
    for pid, hist in series.items():
        # preserve raw history in results but compute forecast from robust values
        raw_units = [u for _, u in hist]
        if not raw_units:
            continue

        # take the last `window` points (or fewer if not available)
        recent = raw_units[-window:] if len(raw_units) >= window else raw_units

        # Adaptive outlier handling: only apply a cap when there are clear extreme
        # outliers relative to the typical scale for this product. This avoids
        # forcing small-series forecasts up to a fixed value like 100.
        # Use numpy when available for robust stats, otherwise fallback to Python stdlib
        try:
            import numpy as np
            med = float(np.median(raw_units))
            mx = float(max(raw_units))
        except Exception:
            import statistics as stats
            med = float(stats.median(raw_units))
            mx = float(max(raw_units))

        cap = None
        # If the maximum is much larger than the median (suggesting a spike),
        # compute a conservative cap using a high percentile of historical data.
        if med > 0 and mx > med * 10 and mx > MAX_UNITS_PER_SALE:
            try:
                import numpy as np
                p95 = float(np.percentile(raw_units, 95))
                cap = int(max(MAX_UNITS_PER_SALE, round(p95)))
            except Exception:
                # Fallback percentile implementation (approximate using sorted values)
                try:
                    sorted_vals = sorted(raw_units)
                    idx = int(round(0.95 * (len(sorted_vals) - 1)))
                    p95 = float(sorted_vals[idx])
                    cap = int(max(MAX_UNITS_PER_SALE, round(p95)))
                except Exception:
                    cap = MAX_UNITS_PER_SALE

        # Apply cap if determined, otherwise use raw values
        if cap:
            capped = [min(int(u), cap) for u in recent]
        else:
            capped = [int(u) for u in recent]

        # Use trimmed mean when there are at least 3 points for robustness
        if len(capped) >= 3:
            sorted_cap = sorted(capped)
            trimmed = sorted_cap[1:-1]
            avg = sum(trimmed) / len(trimmed) if trimmed else (sum(capped) / len(capped))
        else:
            avg = sum(capped) / len(capped)

        forecast = max(0, int(round(avg)))

        # Estimate simple trend and confidence per-product for richer payloads
        trend = 'stable'
        if len(raw_units) >= 2 and raw_units[-1] > raw_units[0]:
            trend = 'increasing'
        elif len(raw_units) >= 2 and raw_units[-1] < raw_units[0]:
            trend = 'decreasing'

        # Confidence: inverse of dispersion
        try:
            try:
                import numpy as np
                variance = float(np.var(capped))
            except Exception:
                import statistics as stats
                variance = float(stats.pvariance(capped)) if len(capped) > 1 else 0.0
            mean = float(avg) if avg else 0.0
            if mean <= 0:
                confidence = 0.0
            else:
                rel_disp = (variance ** 0.5) / mean
                confidence = max(0.0, min(100.0, (1.0 - rel_disp) * 100.0))
        except Exception:
            confidence = 0.0

        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        results[pid] = {"history": hist, "forecast": forecast, "avg": avg, "trend": trend, "confidence": round(confidence, 2), "accuracy": accuracy}
    
    return {
        'db_forecasts': results
    }


def aggregate_sales(period='daily', lookback=90):
    """
    Aggregate sales into time series.
    period: 'daily', 'weekly', or 'monthly'
    lookback: number of days (for daily), weeks (for weekly), months (for monthly)
    Returns list of (label, units) ordered chronologically.
    """
    today = date.today()
    series = []

    # Cap suspiciously large per-sale unit counts to avoid single bad rows
    # from skewing aggregated charts (e.g. mis-imported rows with units_sold >> typical values).
    # This caps each *individual* Sale.units_sold at MAX_UNITS_PER_SALE before summing.
    MAX_UNITS_PER_SALE = 100
    from django.db.models import Case, When, Value, IntegerField

    if period == 'daily':
        start = today - timedelta(days=lookback - 1)
        # Initialize dict with zeros
        counts = { (start + timedelta(days=i)): 0 for i in range(lookback) }
        # Annotate using a capped per-row value so extreme outliers don't dominate totals
        qs = Sale.objects.filter(date__gte=start).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            counts[d] = counts.get(d, 0) + int(row['total'] or 0)
        for d in sorted(counts.keys()):
            series.append((d.isoformat(), counts[d]))

    elif period == 'weekly':
        # Weeks ending on Sunday (use ISO week numbers)
        start = today - timedelta(weeks=lookback - 1)
        # create week start dates
        weeks = []
        for i in range(lookback):
            wk_start = (start + timedelta(weeks=i))
            # normalize to Monday
            wk_start = wk_start - timedelta(days=wk_start.weekday())
            weeks.append(wk_start)
        counts = { w: 0 for w in weeks }
        qs = Sale.objects.filter(date__gte=weeks[0]).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            wk_start = d - timedelta(days=d.weekday())
            if wk_start in counts:
                counts[wk_start] += int(row['total'] or 0)
        for w in sorted(counts.keys()):
            label = w.isoformat()
            series.append((label, counts[w]))

    elif period == 'monthly':
        start = today - relativedelta(months=lookback - 1)
        months = []
        cur = start.replace(day=1)
        for i in range(lookback):
            months.append(cur)
            cur = (cur + relativedelta(months=1)).replace(day=1)
        counts = { m: 0 for m in months }
        qs = Sale.objects.filter(date__gte=months[0]).values('date').annotate(
            total=Sum(Case(
                When(units_sold__gt=MAX_UNITS_PER_SALE, then=Value(MAX_UNITS_PER_SALE)),
                default='units_sold',
                output_field=IntegerField()
            ))
        )
        for row in qs:
            d = row['date']
            m = d.replace(day=1)
            if m in counts:
                counts[m] += int(row['total'] or 0)
        for m in sorted(counts.keys()):
            label = m.strftime('%Y-%m')
            series.append((label, counts[m]))

    return series


def forecast_time_series(series, horizon=7, method='linear', window=3):
    """
    Given a time series list of (label, value), produce a forecast for `horizon` steps ahead.

    Methods:
      - 'linear': fit a linear regression to capture trends (default, best for showing real patterns)
      - 'ma': moving-median / moving-average style (robust to outliers/spikes but flattens trends)

    Returns dict with keys: 'forecast' (list), 'upper', 'lower', 'confidence', 'accuracy'
    """
    # Import numeric libs lazily and tolerate their absence
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        from sklearn.linear_model import LinearRegression
    except Exception:
        LinearRegression = None

    values = [v for _, v in series]
    n = len(values)
    if n == 0:
        return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0}

    # If we have very few data points (less than 2), we can't fit a meaningful linear model
    # Fall back to moving average / median approach
    if n < 2 and method == 'linear':
        method = 'ma'

    if method == 'linear':

        # If linear regression libs are not available, fall back to moving-average method
        if (np is None) or (LinearRegression is None):
            method = 'ma'
        else:
            # Original linear-regression-based implementation
            X = np.arange(n).reshape(-1, 1)
            y = np.array(values, dtype=float)
            try:
                model = LinearRegression()
                model.fit(X, y)
                r2 = model.score(X, y)

                future_X = np.arange(n, n + horizon).reshape(-1, 1)
                preds = model.predict(future_X)
                preds = [max(0, float(round(p))) for p in preds]

                resid = y - model.predict(X)
                std = float(resid.std()) if len(resid) > 1 else max(1.0, float(y.std() if y.size else 1.0))
                upper = [int(round(p + 1.5 * std)) for p in preds]
                lower = [max(0, int(round(p - 1.5 * std))) for p in preds]

                confidence = max(0.0, min(100.0, r2 * 100))
                if confidence >= 70:
                    accuracy = 'High'
                elif confidence >= 40:
                    accuracy = 'Medium'
                else:
                    accuracy = 'Low'

                return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': confidence, 'accuracy': accuracy}
            except Exception:
                # If linear regression fails (e.g., invalid data), fall back to moving average
                method = 'ma'

    # Default: moving-median/average method (robust to spikes)
    # Use the median of the recent `window` points as the forecast value
    try:
        recent = values[-window:] if window and len(values) >= 1 else values
        med = float(np.median(recent)) if recent else 0.0
        
        # Instead of a flat median, create a simple trend: use slope of recent data
        if len(recent) >= 2:
            recent_x = np.arange(len(recent)).reshape(-1, 1)
            recent_y = np.array(recent, dtype=float)
            try:
                trend_model = LinearRegression()
                trend_model.fit(recent_x, recent_y)
                slope = trend_model.coef_[0]
                # Use recent average as base, then apply slope for each forecast step
                preds = [max(0, int(round(med + slope * (i + 1)))) for i in range(horizon)]
            except Exception:
                # If trend estimation fails, use flat median
                preds = [max(0, int(round(med))) for _ in range(horizon)]
        else:
            preds = [max(0, int(round(med))) for _ in range(horizon)]

        # Measure dispersion with std of recent values (or full series if very short)
        disp_source = recent if len(recent) >= 2 else values
        std = float(np.std(disp_source)) if len(disp_source) > 0 else 0.0
        upper = [int(round(p + 1.5 * std)) for p in preds]
        lower = [max(0, int(round(p - 1.5 * std))) for p in preds]

        # Confidence: inverse of normalized dispersion (higher dispersion -> lower confidence)
        if med <= 0:
            confidence = 0.0
        else:
            rel_disp = std / (med + 1e-9)
            confidence = max(0.0, min(100.0, (1.0 - rel_disp) * 100.0))

        if confidence >= 70:
            accuracy = 'High'
        elif confidence >= 40:
            accuracy = 'Medium'
        else:
            accuracy = 'Low'

        return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': confidence, 'accuracy': accuracy}
    except Exception:
        # Fallback safe defaults
        return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0}


def compute_period_overview(series):
    """Given a time series list of (label, units) ordered chronologically,
    return a summary dict with total (most recent), previous total, pct_change and arrow.
    """
    if not series:
        return {'total': 0, 'previous': 0, 'pct_change': 0.0, 'arrow': 'same'}
    # last value is current period
    cur_label, cur_val = series[-1]
    prev_val = series[-2][1] if len(series) >= 2 else 0
    total = int(cur_val)
    previous = int(prev_val)
    if previous == 0:
        pct = 100.0 if total > 0 else 0.0
    else:
        pct = round(((total - previous) / float(previous)) * 100.0, 2)
    if pct > 0:
        arrow = 'up'
    elif pct < 0:
        arrow = 'down'
    else:
        arrow = 'same'
    return {'total': total, 'previous': previous, 'pct_change': pct, 'arrow': arrow}


def generate_insight(period_name, series, forecast_payload):
    """Generate a short insight string for the period based on recent trend and forecast confidence."""
    # Basic heuristics: use last 3 points to detect trend and use forecast_payload['confidence']
    try:
        vals = [v for _, v in series]
        if not vals:
            return ''
        recent = vals[-3:]
        avg_recent = sum(recent) / len(recent)
        forecast_conf = float(forecast_payload.get('confidence', 0))
        # trend check
        if len(vals) >= 3 and vals[-1] > vals[-2] > vals[-3]:
            trend_text = 'increasing'
        elif len(vals) >= 3 and vals[-1] < vals[-2] < vals[-3]:
            trend_text = 'decreasing'
        else:
            trend_text = 'stable'

        if trend_text == 'increasing' and forecast_conf >= 60:
            return f"{period_name.capitalize()} sales show an increasing trend; expected to continue (confidence: {int(forecast_conf)}%)."
        if trend_text == 'decreasing' and forecast_conf >= 60:
            return f"{period_name.capitalize()} sales are decreasing; consider promotions (confidence: {int(forecast_conf)}%)."
        if trend_text == 'stable' and forecast_conf >= 70:
            return f"{period_name.capitalize()} sales are steady; no major changes expected (confidence: {int(forecast_conf)}%)."
        # Low confidence fallback
        if forecast_conf < 40:
            return f"{period_name.capitalize()} forecast has low confidence ({int(forecast_conf)}%). Review recent data for anomalies."
        # General mild insight
        return f"{period_name.capitalize()} sales show {trend_text} behaviour (confidence: {int(forecast_conf)}%)."
    except Exception:
        return ''

