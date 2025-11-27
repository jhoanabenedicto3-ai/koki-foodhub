from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
import logging

from .models import Product, InventoryItem, Sale
from .forms import ProductForm, InventoryForm, SaleForm
from .services.forecasting import moving_average_forecast
from .auth import group_required  # new: role guard

def signup(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')
        
        # Validation
        if not username or not email or not password:
            messages.error(request, 'All fields are required')
            return render(request, 'pages/signup.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match')
            return render(request, 'pages/signup.html')
        
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return render(request, 'pages/signup.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'pages/signup.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'pages/signup.html')

@login_required
def profile(request):
    return render(request, "pages/profile.html", {})

# Dashboard: any authenticated user
@login_required
def dashboard(request):
    top_products = Sale.objects.values("product__name").annotate(
        total_units=Sum("units_sold"), total_revenue=Sum("revenue")
    ).order_by("-total_units")[:5]

    low_stock = [i for i in InventoryItem.objects.select_related("product").all() if i.is_low_stock()]
    
    # Get all products with inventory info
    all_products = Product.objects.all().prefetch_related('inventory_items')
    products_data = []
    categories_set = set()
    
    for product in all_products:
        inv = product.inventory_items.first() if product.inventory_items.exists() else None
        # Normalize name display (replace underscores, title case)
        pretty_name = product.name.replace('_', ' ').title()
        products_data.append({
            'id': product.id,
            'name': pretty_name,
            'price': float(product.price),
            'category': product.category,
            'quantity': inv.quantity if inv else 0,
            'is_low_stock': inv.is_low_stock() if inv else False,
            'image': product.image.url if product.image else None
        })
        categories_set.add(product.category)
    
    # Sort categories for consistent display
    categories = sorted([c for c in categories_set if c])
    
    context = {
        "top_products": top_products,
        "low_stock": low_stock,
        "all_products": products_data,
        "categories": categories
    }
    return render(request, "pages/dashboard.html", context)

# Products: Manager only
@group_required("Manager")
def product_list(request):
    products = Product.objects.all()
    return render(request, "pages/product_list.html", {"products": products})

@group_required("Manager")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created.")
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "pages/product_form.html", {"form": form, "title": "Create Product"})

@group_required("Manager")
def product_update(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated.")
            return redirect("product_list")
    else:
        form = ProductForm(instance=product)
    return render(request, "pages/product_form.html", {"form": form, "title": "Edit Product"})

@group_required("Manager")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "pages/product_form.html", {"form": None, "title": "Delete Product", "confirm": True})

# Inventory: Manager only
@group_required("Manager")
def inventory_list(request):
    items = InventoryItem.objects.select_related("product").all()
    return render(request, "pages/inventory_list.html", {"items": items})

@group_required("Manager")
def inventory_create(request):
    if request.method == "POST":
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item created.")
            return redirect("inventory_list")
    else:
        form = InventoryForm()
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Create Inventory Item"})

@group_required("Manager")
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Inventory item updated.")
            return redirect("inventory_list")
    else:
        form = InventoryForm(instance=item)
    return render(request, "pages/inventory_form.html", {"form": form, "title": "Edit Inventory Item"})

@group_required("Manager")
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Inventory item deleted.")
        return redirect("inventory_list")
    return render(request, "pages/inventory_form.html", {"form": None, "title": "Delete Inventory Item", "confirm": True})

# Sales: Cashier or Manager
@group_required("Cashier", "Manager")
def sale_list(request):
    sales = Sale.objects.select_related("product").all()
    return render(request, "pages/sale_list.html", {"sales": sales})

@group_required("Cashier", "Manager")
def sale_create(request):
    if request.method == "POST":
        form = SaleForm(request.POST)
        if form.is_valid():
            sale = form.save()
            # decrement inventory if exists
            try:
                inv = InventoryItem.objects.get(product=sale.product)
                inv.quantity = max(inv.quantity - sale.units_sold, 0)
                inv.save()
            except InventoryItem.DoesNotExist:
                pass
            messages.success(request, "Sale recorded.")
            return redirect("sale_list")
    else:
        form = SaleForm()
    return render(request, "pages/sale_form.html", {"form": form, "title": "Record Sale"})

@group_required("Cashier", "Manager")
def sale_update(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        form = SaleForm(request.POST, instance=sale)
        if form.is_valid():
            form.save()
            messages.success(request, "Sale updated.")
            return redirect("sale_list")
    else:
        form = SaleForm(instance=sale)
    return render(request, "pages/sale_form.html", {"form": form, "title": "Edit Sale"})

@group_required("Cashier", "Manager")
def sale_delete(request, pk):
    sale = get_object_or_404(Sale, pk=pk)
    if request.method == "POST":
        sale.delete()
        messages.success(request, "Sale deleted.")
        return redirect("sale_list")
    return render(request, "pages/sale_form.html", {"form": None, "title": "Delete Sale", "confirm": True})

# Sales Dashboard: any authenticated user
@login_required
def sales_dashboard(request):
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models.functions import TruncDate

    # Total sales and orders
    total_sales = Sale.objects.aggregate(total_revenue=Sum('revenue'))['total_revenue'] or 0
    total_orders = Sale.objects.count()
    avg_order = (total_sales / total_orders) if total_orders else 0

    # Top selling items (by units)
    top_items_qs = (
        Sale.objects.values('product__name')
        .annotate(units_sold=Sum('units_sold'), revenue=Sum('revenue'))
        .order_by('-units_sold')[:5]
    )
    top_items = [{'product': t['product__name'], 'units': t['units_sold'], 'revenue': float(t['revenue'])} for t in top_items_qs]

    # Recent sales history (last 20 sale records)
    recent_qs = Sale.objects.select_related('product').order_by('-id')[:20]
    recent_sales = []
    for s in recent_qs:
        # Format time in a portable way: avoid platform-specific flags like '%-I'
        time_str = ''
        if getattr(s, 'date', None):
            try:
                # Use %I for hour (12-hour clock) and strip any leading zero for prettier display
                time_str = s.date.strftime('%I:%M:%S %p').lstrip('0')
            except Exception:
                # Fallback to ISO format if strftime fails for any reason
                time_str = getattr(s, 'date').isoformat()

        recent_sales.append({
            'item': s.product.name,
            'qty': s.units_sold,
            'price': float(s.revenue) / s.units_sold if s.units_sold else 0,
            'total': float(s.revenue),
            'time': time_str
        })

    # Sales by category (sum units and revenue)
    cat_qs = (
        Sale.objects.select_related('product')
        .values('product__category')
        .annotate(units=Sum('units_sold'), revenue=Sum('revenue'))
    )
    category_sales = []
    for c in cat_qs:
        category_sales.append({'category': c['product__category'] or 'Uncategorized', 'quantity': int(c['units'] or 0), 'revenue': float(c['revenue'] or 0)})

    # Daily totals (last 7 days)
    today = timezone.now().date()
    start_date = today - timedelta(days=6)
    try:
        daily_qs = (
            Sale.objects.filter(date__gte=start_date)
            .annotate(day=TruncDate('date'))
            .values('day')
            .annotate(total_revenue=Sum('revenue'), total_orders=Count('id'))
            .order_by('day')
        )
        daily_sales = [
            {
                'day': d['day'],
                'revenue': float(d['total_revenue'] or 0),
                'orders': int(d['total_orders'] or 0)
            }
            for d in daily_qs
        ]
    except Exception as e:
        logging.getLogger(__name__).exception('Failed to compute daily_sales: %s', e)
        daily_sales = []

    # Weekly totals (last 4 weeks) - compute in Python to avoid DB-specific TruncWeek issues
    start_week = today - timedelta(weeks=3)
    weekly_sales = []
    try:
        weekly_map = {}
        sales_for_weeks = Sale.objects.filter(date__gte=start_week).values('date', 'revenue')
        for rec in sales_for_weeks:
            d = rec.get('date')
            if d is None:
                continue
            # Normalize to date if datetime
            if hasattr(d, 'date'):
                d = d.date()
            # Compute week start (Monday)
            week_start = d - timedelta(days=d.weekday())
            entry = weekly_map.setdefault(week_start, {'revenue': 0.0, 'orders': 0})
            entry['revenue'] += float(rec.get('revenue') or 0)
            entry['orders'] += 1

        weekly_sales = [
            {'week_start': wk, 'revenue': data['revenue'], 'orders': data['orders']}
            for wk, data in sorted(weekly_map.items())
        ]
    except Exception as e:
        logging.getLogger(__name__).exception('Failed to compute weekly_sales: %s', e)
        weekly_sales = []

    # Prepare context
    # Compute explicit today totals so client can rely on server-defined "today"
    today_entry = next((d for d in daily_sales if d.get('day') == today), None) if daily_sales else None
    today_orders = int(today_entry['orders']) if today_entry else 0
    today_revenue = float(today_entry['revenue']) if today_entry else 0.0
    today_label = str(today)
    # Provide a server-side ISO timestamp so the client can use the server's notion of "now"
    server_today_iso = timezone.now().isoformat()
    context = {
        'total_sales': float(total_sales),
        'total_orders': int(total_orders),
        'avg_order': float(avg_order),
        'top_items': top_items,
        'recent_sales': recent_sales,
        'category_sales': category_sales,
        'daily_sales': daily_sales,
        'weekly_sales': weekly_sales,
        'today_label': today_label,
        'today_orders': today_orders,
        'today_revenue': today_revenue,
        'server_today_iso': server_today_iso,
    }
    return render(request, "pages/sales_dashboard.html", context)

# Forecast: Manager only
@group_required("Manager")
def forecast_view(request):
    from .services.forecasting import get_csv_forecast
    from datetime import datetime, timedelta
    
    # Get CSV-based forecasts (real data)
    csv_data = get_csv_forecast()
    
    # Get database forecasts
    db_results = moving_average_forecast(window=3)
    db_forecasts = db_results.get('db_forecasts', {})
    
    # Prepare data for template
    data = []
    
    # Add CSV forecasts
    for product_name, forecast_info in csv_data.items():
        # Ensure confidence is a percentage (0-100)
        confidence = forecast_info['confidence']
        if confidence < 1:  # If it's still in decimal format (0-1), convert to percentage
            confidence = confidence * 100
        
        data.append({
            "product": product_name,
            "forecast": forecast_info['forecast'],
            "avg": forecast_info['avg'],
            "trend": forecast_info['trend'],
            "confidence": confidence,
            "history": forecast_info['history'],
            "last_7_days": forecast_info['last_7_days'],
            "source": "Real Data (CSV)",
            "is_csv": True
        })
    
    # Calculate analytics
    total_forecasted_units = sum(item['forecast'] for item in data)
    avg_confidence = sum(item['confidence'] for item in data) / len(data) if data else 0
    
    # Calculate next week forecast (7 days)
    next_week_forecast = total_forecasted_units * 7
    
    # Determine peak day (Saturday is typically busier)
    peak_day = "Saturday"
    peak_orders = int(total_forecasted_units * 1.2)  # 20% increase on peak day
    
    # Calculate week-over-week growth
    last_week_total = sum(item['last_7_days'] for item in data)
    growth_percentage = ((next_week_forecast - last_week_total) / last_week_total * 100) if last_week_total > 0 else 0
    
    context = {
        "data": data,
        "total_forecast": next_week_forecast,
        "avg_confidence": avg_confidence,
        "peak_day": peak_day,
        "peak_orders": peak_orders,
        "growth_percentage": growth_percentage,
        "currency": "₱"
    }
    return render(request, "pages/forecast.html", context)
    # Add database forecasts as fallback
    for pid, r in db_forecasts.items():
        try:
            product = Product.objects.get(pk=pid)
            data.append({
                "product": product.name,
                "forecast": r["forecast"],
                "avg": r["avg"],
                "trend": "unknown",
                "confidence": 0,
                "history": r["history"],
                "last_7_days": sum([u for _, u in r["history"][-7:]]),
                "source": "Database",
                "is_csv": False
            })
        except Product.DoesNotExist:
            pass
    return render(request, "pages/forecast.html", {"data": data})

@login_required
def create_sale(request):
    """API endpoint to create a sale transaction"""
    from django.http import JsonResponse
    from django.views.decorators.http import require_http_methods
    import json
    logging.getLogger(__name__).info('create_sale called by user: %s, method: %s', getattr(request,'user',None), request.method)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logging.getLogger(__name__).info('create_sale payload: %s', data)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'error': 'No items in cart'}, status=400)
            
            # Create sale records for each item
            for item in items:
                product = Product.objects.get(pk=item['id'])
                sale = Sale.objects.create(
                    product=product,
                    units_sold=item['quantity'],
                    revenue=float(item['price']) * item['quantity']
                )
                
                # Update inventory
                inv = product.inventory_items.first()
                if inv:
                    inv.quantity -= item['quantity']
                    inv.save()
            
            return JsonResponse({'success': True, 'message': 'Sale recorded successfully'})
        except Product.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)
