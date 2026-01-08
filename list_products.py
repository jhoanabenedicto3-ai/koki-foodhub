import sqlite3

conn = sqlite3.connect('db.sqlite3')
cursor = conn.cursor()
cursor.execute("SELECT id, name FROM core_product ORDER BY name")
print('All products:')
for row in cursor.fetchall():
    print(f'  ID {row[0]}: {row[1]}')
conn.close()
