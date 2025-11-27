
from django import forms
from .models import Product, InventoryItem, Sale

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category", "price", "is_active", "image"]
        widgets = {
            "name": forms.TextInput(attrs={"class":"input"}),
            "category": forms.TextInput(attrs={"class":"input"}),
            "price": forms.NumberInput(attrs={"class":"input","step":"0.01"}),
            "image": forms.FileInput(attrs={"class":"input"}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = ["product", "sku", "quantity", "reorder_point"]
        widgets = {
            "product": forms.Select(attrs={"class":"input"}),
            "sku": forms.TextInput(attrs={"class":"input"}),
            "quantity": forms.NumberInput(attrs={"class":"input"}),
            "reorder_point": forms.NumberInput(attrs={"class":"input"}),
        }

class SaleForm(forms.ModelForm):
    class Meta:
        model = Sale
        fields = ["product", "date", "units_sold", "revenue"]
        widgets = {
            "product": forms.Select(attrs={"class":"input"}),
            "date": forms.DateInput(attrs={"class":"input","type":"date"}),
            "units_sold": forms.NumberInput(attrs={"class":"input"}),
            "revenue": forms.NumberInput(attrs={"class":"input","step":"0.01"}),
        }
