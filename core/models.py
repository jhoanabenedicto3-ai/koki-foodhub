# core/models.py
from django.db import models
from django.utils import timezone

class Product(models.Model):
    name = models.CharField(max_length=120)
    category = models.CharField(max_length=80, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    def __str__(self):
        return self.name

class InventoryItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_items")
    sku = models.CharField(max_length=64, unique=True)
    quantity = models.PositiveIntegerField(default=0)
    reorder_point = models.PositiveIntegerField(default=10)
    updated_at = models.DateTimeField(auto_now=True)

    def is_low_stock(self):
        return self.quantity <= self.reorder_point

    def __str__(self):
        return f"{self.sku} - {self.product.name}"

class Sale(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="sales")
    date = models.DateField(default=timezone.now)
    units_sold = models.PositiveIntegerField()
    revenue = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.product.name} - {self.date} - {self.units_sold}"
