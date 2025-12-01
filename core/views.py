from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum
from django.db.models.functions import Lower
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import logging
import json
from django.http import JsonResponse
from django.contrib.auth import logout as auth_logout

from .models import Product, InventoryItem, Sale
from .forms import ProductForm, InventoryForm, SaleForm
from .services.forecasting import moving_average_forecast
from .auth import group_required  # new: role guard
from django.views.decorators.http import require_http_methods

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

        # Assign selected role/group if provided. Allowed roles: Cashier and Owner.
        role = request.POST.get('role', '').strip()
        if role == 'Owner':
            grp, _ = Group.objects.get_or_create(name='Owner')
            user.groups.add(grp)
            user.save()
            # Owner accounts can login immediately
            try:
                auth_user = authenticate(request, username=username, password=password)
                if auth_user:
                    auth_login(request, auth_user)
                    messages.success(request, 'Owner account created and logged in successfully!')
                    return redirect('dashboard')
            except Exception:
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')

        elif role == 'Cashier':
            # Cashier registrations require Owner approval. Create user as inactive
            # and add to a 'PendingCashier' group so owners can review and approve.
            pending_grp, _ = Group.objects.get_or_create(name='PendingCashier')
            user.groups.add(pending_grp)
            user.is_active = False
            user.save()
            messages.success(request, 'Account created and is pending Owner approval. You will be notified when approved.')
            return redirect('login')

        else:
            # No role selected or unknown role — create account without group and allow login
            try:
                auth_user = authenticate(request, username=username, password=password)
                if auth_user:
                    auth_login(request, auth_user)
                    messages.success(request, 'Account created and logged in successfully!')
                    return redirect('dashboard')
            except Exception:
                messages.success(request, 'Account created successfully! Please login.')
                return redirect('login')
    
    return render(request, 'pages/signup.html')


def logout_view(request):
    """Log out the user on GET or POST and redirect to login."""
    try:
        auth_logout(request)
    except Exception:
        pass
    return redirect('login')

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
        # Normalize name display (replace underscores, title case) - WITHOUT the size suffix
        pretty_name = product.name.replace('_', ' ').title()
        
        # Build size-price mapping with automatic multipliers
        # Small: base - 5, Medium: Regular + 5, Large: base + 10
        base_price = float(product.price)
        size_prices = {}
        if product.size:
            size_prices = {
                'S': max(0, base_price - 5),        # Small: -5
                'M': base_price + 5,                 # Medium: Regular +5
                'L': base_price + 10,                # Large: +10
                'XL': base_price + 15,               # XL: +15 (bonus)
                'XXL': base_price + 20,              # XXL: +20 (bonus)
                'Regular': base_price,               # Regular: base
            }
        
        products_data.append({
            'id': product.id,
            'name': pretty_name,
            'price': base_price,
            'category': product.category,
            'size': product.size,
            'size_prices': size_prices,
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

# Products: Admin only (read), Cashier can view
@group_required("Admin", "Cashier")
def product_list(request):
    # Cashier can only view, not edit. Check in template if user is admin for edit buttons
    # Support server-side sorting using ?sort=price-asc|price-desc|name|newest
    sort = request.GET.get('sort', '')
    products = Product.objects.all()
    if sort == 'price-asc':
        products = products.order_by('price')
    elif sort == 'price-desc':
        products = products.order_by('-price')
    elif sort == 'name':
        # Case-insensitive alphabetical sort so lowercase names (e.g. "burger")
        # appear in the expected A → Z order.
        products = products.order_by(Lower('name'))
    elif sort == 'newest':
        # uses created_at for accurate ordering
        products = products.order_by('-created_at')

    return render(request, "pages/product_list.html", {"products": products, "sort": sort})

@group_required("Admin", "Cashier")
def product_create(request):
    if request.method == "POST":
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            # Ensure created_at is set
            if not product.created_at:
                from django.utils import timezone
                product.created_at = timezone.now()
            product.save()
            messages.success(request, "Product created.")
            return redirect("product_list")
    else:
        form = ProductForm()
    return render(request, "pages/product_form.html", {"form": form, "title": "Create Product"})

@group_required("Admin", "Cashier")
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

@group_required("Admin", "Cashier")
def product_delete(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == "POST":
        product.delete()
        messages.success(request, "Product deleted.")
        return redirect("product_list")
    return render(request, "pages/product_form.html", {"form": None, "title": "Delete Product", "confirm": True})

# Inventory: Admin only
@group_required("Admin")
def inventory_list(request):
    items = InventoryItem.objects.select_related("product").all()
    return render(request, "pages/inventory_list.html", {"items": items})

@group_required("Admin")
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

@group_required("Admin")
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

@group_required("Admin")
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == "POST":
        item.delete()
        messages.success(request, "Inventory item deleted.")
        return redirect("inventory_list")
    return render(request, "pages/inventory_form.html", {"form": None, "title": "Delete Inventory Item", "confirm": True})

# Sales: Admin only (Cashier should not access sales list page)
@group_required("Admin")
def sale_list(request):
    sales = Sale.objects.select_related("product").all()
    return render(request, "pages/sale_list.html", {"sales": sales})

@group_required("Admin")
@group_required("Admin", "Cashier")
def sale_create(request):
    # Redirect to the sales period form for automatic reporting
    return redirect('record_sales_period')

@group_required("Admin")
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

@group_required("Admin")
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
    # Use server local date to match how dates are stored/displayed
    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()
    start_date = today - timedelta(days=6)
    try:
        # Avoid DB-specific TruncDate by aggregating in Python which is portable across backends
        sales_for_days = Sale.objects.filter(date__gte=start_date).values('date', 'revenue')
        day_map = {}
        for rec in sales_for_days:
            d = rec.get('date')
            if d is None:
                continue
            # ensure d is a date
            if hasattr(d, 'date'):
                d = d.date()
            entry = day_map.setdefault(d, {'revenue': 0.0, 'orders': 0})
            entry['revenue'] += float(rec.get('revenue') or 0)
            entry['orders'] += 1

        daily_sales = [
            {'day': day, 'revenue': data['revenue'], 'orders': data['orders']}
            for day, data in sorted(day_map.items())
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
    # Compute explicit today totals so client can rely on server-defined "today".
    # Use a direct DB aggregate to avoid DB-function issues (e.g. TruncDate failing on SQLite).
    try:
        today_agg = Sale.objects.filter(date=today).aggregate(today_revenue=Sum('revenue'), today_orders=Count('id'))
        today_orders = int(today_agg.get('today_orders') or 0)
        today_revenue = float(today_agg.get('today_revenue') or 0.0)
    except Exception:
        # Fallback to daily_sales if the aggregate fails
        today_entry = next((d for d in daily_sales if d.get('day') == today), None) if daily_sales else None
        today_orders = int(today_entry['orders']) if today_entry else 0
        today_revenue = float(today_entry['revenue']) if today_entry else 0.0
    today_label = str(today)
    # Provide a server-side ISO timestamp so the client can use the server's notion of "now"
    server_today_iso = timezone.localtime().isoformat()
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


@login_required
def sales_today_api(request):
    """Return JSON with today's sales totals (orders, revenue) and server timestamp."""
    from django.utils import timezone
    from django.db.models import Sum, Count

    try:
        today = timezone.localdate()
    except Exception:
        today = timezone.now().date()

    try:
        agg = Sale.objects.filter(date=today).aggregate(today_revenue=Sum('revenue'), today_orders=Count('id'))
        orders = int(agg.get('today_orders') or 0)
        revenue = float(agg.get('today_revenue') or 0.0)
    except Exception:
        orders = 0
        revenue = 0.0

    server_today_iso = timezone.localtime().isoformat()
    return JsonResponse({'orders': orders, 'revenue': revenue, 'server_today_iso': server_today_iso})

# Forecast: Admin only
@group_required("Admin")
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


# Admin: user management (Admin only)
@group_required("Admin")
def admin_user_list(request):
    users = User.objects.all().prefetch_related('groups')
    users_info = []
    for u in users:
        users_info.append({
            'user': u,
            'is_admin': u.groups.filter(name='Admin').exists(),
            'is_cashier': u.groups.filter(name='Cashier').exists(),
        })
    return render(request, 'pages/admin_user_list.html', {'users': users_info})


@group_required("Admin")
@require_http_methods(["POST"])
def admin_toggle_group(request):
    user_id = request.POST.get('user_id')
    group_name = request.POST.get('group')
    action = request.POST.get('action')  # 'add' or 'remove'
    user = get_object_or_404(User, pk=user_id)
    try:
        group = Group.objects.get(name=group_name)
    except Group.DoesNotExist:
        messages.error(request, f"Group '{group_name}' does not exist.")
        return redirect('admin_user_list')

    # Perform the requested action
    if action == 'add':
        user.groups.add(group)
        msg = f"Added {user.username} to {group.name}."
        messages.success(request, msg)
    else:
        user.groups.remove(group)
        msg = f"Removed {user.username} from {group.name}."
        messages.success(request, msg)

    # If AJAX request, return JSON for client-side updates
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'ok',
            'message': msg,
            'user_id': user.id,
            'group': group.name,
            'is_admin': user.groups.filter(name='Admin').exists(),
            'is_cashier': user.groups.filter(name='Cashier').exists(),
        })

    return redirect('admin_user_list')


# Record sales by period (week/month) - Auto-summarize and printable
@group_required("Admin")
def record_sales_period(request):
    """Record sales summary for a week or month with printable option"""
    from datetime import timedelta
    
    if request.method == 'POST':
        # Get period from form and determine action
        period = request.POST.get('period', 'week')
        action = request.POST.get('action', 'view')  # 'view' or 'print'
        
        # Get the date range
        today = timezone.now().date()
        if period == 'week':
            start_date = today - timedelta(days=today.weekday())  # Monday of this week
            end_date = start_date + timedelta(days=6)  # Sunday
        else:  # month
            start_date = today.replace(day=1)
            if today.month == 12:
                end_date = start_date.replace(year=today.year + 1, month=1) - timedelta(days=1)
            else:
                end_date = start_date.replace(month=today.month + 1) - timedelta(days=1)
        
        # Get sales for the period
        sales = Sale.objects.filter(date__gte=start_date, date__lte=end_date)
        
        # Calculate totals
        total_units = sales.aggregate(Sum('units_sold'))['units_sold__sum'] or 0
        total_revenue = sales.aggregate(Sum('revenue'))['revenue__sum'] or 0
        
        # Group by product
        sales_by_product = sales.values('product__name').annotate(
            units=Sum('units_sold'),
            revenue=Sum('revenue')
        ).order_by('-revenue')
        
        context = {
            'period': period,
            'start_date': start_date,
            'end_date': end_date,
            'total_units': total_units,
            'total_revenue': total_revenue,
            'sales_by_product': list(sales_by_product),
            'sales_count': sales.count(),
            'now': timezone.now(),
        }
        
        if action == 'print':
            # Return printable version
            return render(request, 'pages/sales_report_print.html', context)
        else:
            return render(request, 'pages/sales_report.html', context)
    
    return render(request, 'pages/sales_period_form.html')

@group_required("Admin")
def api_record_sales_summary(request):
    """API endpoint to record sales summary and return as JSON for printing"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            period = data.get('period', 'week')  # 'week' or 'month'
            
            from datetime import timedelta
            today = timezone.now().date()
            if period == 'week':
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # month
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = start_date.replace(year=today.year + 1, month=1) - timedelta(days=1)
                else:
                    end_date = start_date.replace(month=today.month + 1) - timedelta(days=1)
            
            sales = Sale.objects.filter(date__gte=start_date, date__lte=end_date)
            
            total_units = sales.aggregate(Sum('units_sold'))['units_sold__sum'] or 0
            total_revenue = sales.aggregate(Sum('revenue'))['revenue__sum'] or 0
            
            sales_by_product = list(sales.values('product__name').annotate(
                units=Sum('units_sold'),
                revenue=Sum('revenue')
            ).order_by('-revenue'))
            
            return JsonResponse({
                'success': True,
                'period': period,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_units': total_units,
                'total_revenue': float(total_revenue),
                'sales_by_product': sales_by_product,
                'sales_count': sales.count(),
            })
        except Exception as e:
            logging.error('Error in api_record_sales_summary: %s', str(e))
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Owner: Approve/Reject pending cashier signups
@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_approve(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    try:
        pending = Group.objects.get(name='PendingCashier')
    except Group.DoesNotExist:
        pending = None
    cashier_grp, _ = Group.objects.get_or_create(name='Cashier')
    # Move user from pending to cashier and activate
    if pending:
        user.groups.remove(pending)
    user.groups.add(cashier_grp)
    user.is_active = True
    user.save()
    messages.success(request, f"Approved cashier: {user.username}")
    return redirect('pending_cashiers')


@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_reject(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    # Delete the user (reject)
    username = user.username
    user.delete()
    messages.success(request, f"Rejected and removed user: {username}")
    return redirect('pending_cashiers')

@csrf_exempt
def create_sale(request):
    """API endpoint to create a sale transaction"""
    import json
    import traceback
    
    logger = logging.getLogger(__name__)
    
    # Check if user is authenticated
    if not request.user.is_authenticated:
        logger.warning('create_sale: Unauthenticated user attempting to create sale')
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            logger.info('create_sale payload: %s', data)
            items = data.get('items', [])
            
            if not items:
                logger.warning('create_sale: No items in cart')
                return JsonResponse({'error': 'No items in cart'}, status=400)
            
            # First, validate all items have sufficient inventory
            for item in items:
                try:
                    product = Product.objects.get(pk=item['id'])
                    inv = product.inventory_items.first()
                    
                    if inv and inv.quantity < item['quantity']:
                        logger.warning(f'create_sale: Insufficient inventory for {product.name}')
                        return JsonResponse({'error': f'Insufficient inventory for {product.name}. Available: {inv.quantity}, Requested: {item["quantity"]}'}, status=400)
                    
                    # Validate quantity is positive
                    if item['quantity'] <= 0:
                        logger.warning(f'create_sale: Invalid quantity for {product.name}')
                        return JsonResponse({'error': f'Invalid quantity for {product.name}'}, status=400)
                except Product.DoesNotExist:
                    logger.error(f'create_sale: Product not found with id {item["id"]}')
                    return JsonResponse({'error': f'Product not found (id: {item["id"]})'}, status=404)
            
            # All validations passed, create sale records for each item
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
                    logger.info(f'create_sale: Updated inventory for {product.name}, new qty: {inv.quantity}')
            
            logger.info('create_sale: Sale recorded successfully')
            return JsonResponse({'success': True, 'message': 'Sale recorded successfully'})
        except json.JSONDecodeError as e:
            logger.error('create_sale: JSON decode error: %s', str(e))
            logger.error(f'Request body: {request.body}')
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        except Exception as e:
            logger.error('='*60)
            logger.error('UNHANDLED EXCEPTION in create_sale')
            logger.error('Error: %s', str(e))
            logger.error('Traceback:\n%s', traceback.format_exc())
            logger.error('='*60)
            # Return error without exposing internals in production
            return JsonResponse({'error': f'Server error: {str(e)[:100]}'}, status=500)
    
    logger.warning('create_sale: Method not allowed')
    return JsonResponse({'error': 'Method not allowed'}, status=405)


# Owner: Approve/Reject pending cashier signups
@group_required("Owner")
def pending_cashiers(request):
    try:
        pending_group = Group.objects.get(name='PendingCashier')
        users = pending_group.user_set.all().order_by('username')
    except Group.DoesNotExist:
        users = []
    return render(request, 'pages/pending_cashiers.html', {'users': users})


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_approve(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    try:
        pending = Group.objects.get(name='PendingCashier')
    except Group.DoesNotExist:
        pending = None
    cashier_grp, _ = Group.objects.get_or_create(name='Cashier')
    # Move user from pending to cashier and activate
    if pending:
        user.groups.remove(pending)
    user.groups.add(cashier_grp)
    user.is_active = True
    user.save()
    messages.success(request, f"Approved cashier: {user.username}")
    return redirect('pending_cashiers')


@group_required("Owner")
@require_http_methods(["POST"])
def pending_cashier_reject(request):
    user_id = request.POST.get('user_id')
    user = get_object_or_404(User, pk=user_id)
    # Delete the user (reject)
    username = user.username
    user.delete()
    messages.success(request, f"Rejected and removed user: {username}")
    return redirect('pending_cashiers')

@login_required
def recent_orders_api(request):
    """Return recent sales (last 50 orders) with product details, ordered by most recent first."""
    try:
        # Get the 50 most recent sales, ordered by date (newest first)
        recent_sales = Sale.objects.select_related('product').order_by('-date')[:50]
        
        orders = []
        for sale in recent_sales:
            orders.append({
                'id': sale.id,
                'product_name': sale.product.name,
                'category': sale.product.category,
                'units_sold': sale.units_sold,
                'revenue': float(sale.revenue),
                'date': sale.date.isoformat(),
                'date_formatted': sale.date.strftime('%b %d, %I:%M %p')
            })
        
        return JsonResponse({'success': True, 'orders': orders})
    except Exception as e:
        import traceback
        logger = logging.getLogger(__name__)
        logger.error('Error in recent_orders_api: %s', str(e))
        logger.error('Traceback:\n%s', traceback.format_exc())
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
