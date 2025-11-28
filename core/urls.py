from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView   # 👈 import here

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("signup/", views.signup, name="auth_signup"),
    # Products
    path("products/", views.product_list, name="product_list"),
    path("products/create/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_update, name="product_update"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    # Inventory
    path("inventory/", views.inventory_list, name="inventory_list"),
    path("inventory/create/", views.inventory_create, name="inventory_create"),
    path("inventory/<int:pk>/edit/", views.inventory_update, name="inventory_update"),
    path("inventory/<int:pk>/delete/", views.inventory_delete, name="inventory_delete"),
    # Sales
    path("sales/", views.sale_list, name="sale_list"),
    path("sales/create/", views.sale_create, name="sale_create"),
    path("sales/api/create/", views.create_sale, name="api_create_sale"),
    path("sales/<int:pk>/edit/", views.sale_update, name="sale_update"),
    path("sales/<int:pk>/delete/", views.sale_delete, name="sale_delete"),
    path("sales-dashboard/", views.sales_dashboard, name="sales_dashboard"),
    path("api/sales/today/", views.sales_today_api, name="api_sales_today"),
    # Forecast
    path("forecast/", views.forecast_view, name="forecast"),
    # Auth
    path("logout/", LogoutView.as_view(next_page="/"), name="logout"),   # 👈 added logout
]
