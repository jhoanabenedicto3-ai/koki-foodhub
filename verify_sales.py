import sqlite3
from datetime import date, timedelta

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
today = date.today()

# Verify all sales
cursor.execute("""
SELECT date, core_product.name, SUM(units_sold) 
FROM core_sale 
JOIN core_product ON core_sale.product_id = core_product.id 
WHERE date >= ? 
GROUP BY date, core_product.name 
ORDER BY core_product.name, date
""", ((today - timedelta(days=7)).isoformat(),))

print('Sales in last 7 days by product:')
total_by_product = {}
for row in cursor.fetchall():
    print(f'  {row[0]}: {row[1]:12} - {row[2]:2} units')
    if row[1] not in total_by_product:
        total_by_product[row[1]] = 0
    total_by_product[row[1]] += row[2]

print('\nTotal by product (last 7 days):')
for prod, total in total_by_product.items():
    print(f'  {prod}: {total} units')

conn.close()
