from datetime import date, timedelta
from collections import defaultdict
import os
import csv
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from ..models import Sale, Product
from django.db.models import Sum
from datetime import datetime
from dateutil.relativedelta import relativedelta

def load_csv_data(csv_path=None):
    """Load sales data from CSV file"""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), '../../pizzaplace.csv')
    
    if not os.path.exists(csv_path):
        return None
    
    try:
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'])
        return df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None

def get_csv_forecast(csv_path=None):
    """
    Train ML model on CSV data and return forecasts for each product
    Returns dict: product_name -> { 'forecast': units, 'trend': str, 'confidence': float, 'history': [...] }
    """
    df = load_csv_data(csv_path)
    if df is None:
        return {}
    
    results = {}
    
    # Group by product name
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
        
        results[product_name] = {
            'forecast': forecast,
            'trend': trend,
            'confidence': confidence,
            'history': history,
            'avg': float(y.mean()),
            'last_7_days': int(y[-7:].sum())
        }
    
    return results

def moving_average_forecast(window=3, lookback_days=21):
    """
    Returns dict: product_id -> { 'history': [(date, units)], 'forecast': int, 'avg': float }
    Simple moving average over last `window` sales entries within `lookback_days`.
    Also includes CSV-trained forecasts.
    """
    start = date.today() - timedelta(days=lookback_days)
    sales = Sale.objects.filter(date__gte=start).order_by("product_id", "date")
    series = defaultdict(list)

    for s in sales:
        series[s.product_id].append((s.date, s.units_sold))

    results = {}
    for pid, hist in series.items():
        last_units = [u for _, u in hist][-window:] if len(hist) >= window else [u for _, u in hist]
        if not last_units:
            continue
        avg = sum(last_units) / len(last_units)
        forecast = round(avg)
        results[pid] = {"history": hist, "forecast": forecast, "avg": avg}
    
    # Also get CSV-based forecasts
    csv_forecasts = get_csv_forecast()
    
    return {
        'db_forecasts': results,
        'csv_forecasts': csv_forecasts
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
    if period == 'daily':
        start = today - timedelta(days=lookback - 1)
        # Initialize dict with zeros
        counts = { (start + timedelta(days=i)): 0 for i in range(lookback) }
        qs = Sale.objects.filter(date__gte=start).values('date').annotate(total=Sum('units_sold'))
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
        qs = Sale.objects.filter(date__gte=weeks[0]).values('date').annotate(total=Sum('units_sold'))
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
        qs = Sale.objects.filter(date__gte=months[0]).values('date').annotate(total=Sum('units_sold'))
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
    Given a time series of numeric values, produce a forecast for `horizon` steps ahead.
    Returns dict with 'forecast' list and 'upper' and 'lower' bounds.
    """
    import numpy as np
    from sklearn.linear_model import LinearRegression

    values = [v for _, v in series]
    n = len(values)
    if n == 0:
        return {'forecast': [0] * horizon, 'upper': [0] * horizon, 'lower': [0] * horizon, 'confidence': 0}

    X = np.arange(n).reshape(-1, 1)
    y = np.array(values)

    # Use linear regression for trend
    model = LinearRegression()
    model.fit(X, y)
    r2 = model.score(X, y)

    future_X = np.arange(n, n + horizon).reshape(-1, 1)
    preds = model.predict(future_X)
    preds = [max(0, float(round(p))) for p in preds]

    # Compute simple bounds using std deviation
    resid = y - model.predict(X)
    std = float(resid.std()) if len(resid) > 1 else max(1.0, float(y.std() if y.size else 1.0))
    upper = [int(round(p + 1.5 * std)) for p in preds]
    lower = [max(0, int(round(p - 1.5 * std))) for p in preds]

    confidence = max(0.0, min(100.0, r2 * 100))
    return {'forecast': preds, 'upper': upper, 'lower': lower, 'confidence': confidence}

