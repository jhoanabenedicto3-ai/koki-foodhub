from datetime import date, timedelta
from collections import defaultdict
import os
import csv
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from ..models import Sale, Product

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

