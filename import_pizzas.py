import os
import django
import csv
import pandas as pd

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from core.models import Product, InventoryItem
import uuid

# Read CSV
df = pd.read_csv('pizzaplace.csv')

# Get unique products (name, type, price)
unique_products = df.drop_duplicates(subset=['name']).sort_values('name')

# Category mapping from 'type' column
category_map = {
    'classic': 'Main',
    'veggie': 'Appetizer',
    'chicken': 'Main',
    'supreme': 'Main'
}

print(f"Found {len(unique_products)} unique products")

# Import products
created_count = 0
for _, row in unique_products.iterrows():
    product_name = row['name']
    product_type = row['type']
    product_price = float(row['price'])
    
    # Map category
    category = category_map.get(product_type, 'Main')
    
    # Check if product already exists
    if not Product.objects.filter(name=product_name).exists():
        product = Product.objects.create(
            name=product_name.replace('_', ' ').title(),
            price=product_price,
            category=category
        )
        
        # Create inventory entry with unique SKU
        sku = f"PIZZA-{uuid.uuid4().hex[:8].upper()}"
        InventoryItem.objects.create(
            product=product,
            sku=sku,
            quantity=50,  # Default stock
            reorder_point=10
        )
        
        created_count += 1
        print(f"✓ Created: {product.name} (${product_price}) - {category}")
    else:
        print(f"- Skipped: {product_name} (already exists)")

print(f"\n{created_count} products imported successfully!")
