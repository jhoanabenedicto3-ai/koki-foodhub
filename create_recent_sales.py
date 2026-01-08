import sqlite3
from datetime import date, timedelta
import random

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()

# Get product IDs for fries and carbonara - use the main ones (not test duplicates)
cursor.execute("SELECT id FROM core_product WHERE name IN ('fries', 'carbonara') AND id < 150 ORDER BY id")
products = cursor.fetchall()

if not products:
    print('Products not found')
else:
    today = date.today()
    # Create sales for last 7 days for each product
    for product_id, in products:
        for i in range(7):
            sale_date = today - timedelta(days=6-i)
            units = random.randint(1, 5)
            revenue = units * 5.0
            # INSERT INTO core_sale (product_id, units_sold, revenue, date, timestamp)
            cursor.execute(
                'INSERT INTO core_sale (product_id, units_sold, revenue, date, timestamp) VALUES (?, ?, ?, ?, ?)',
                (product_id, units, revenue, sale_date.isoformat(), f'{sale_date}T12:00:00')
            )
    
    conn.commit()
    print(f'Created test sales for last 7 days')
    
    # Verify
    cursor.execute('SELECT COUNT(*) FROM core_sale WHERE date >= ?', ((today - timedelta(days=7)).isoformat(),))
    count = cursor.fetchone()[0]
    print(f'Total sales in last 7 days now: {count}')
    
    # Show what we created
    cursor.execute("SELECT date, core_product.name, SUM(units_sold) FROM core_sale JOIN core_product ON core_sale.product_id = core_product.id WHERE date >= ? GROUP BY date, core_product.name ORDER BY date", ((today - timedelta(days=7)).isoformat(),))
    print('\nSales by date and product:')
    for row in cursor.fetchall():
        print(f'  {row[0]}: {row[1]} - {row[2]} units')

conn.close()
