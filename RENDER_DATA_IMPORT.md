# RENDER DATABASE IMPORT GUIDE

Your local database has been exported and pushed to GitHub:
- **258 Products**
- **262 Sales Records**  
- **133 Inventory Items**

## Option 1: Use Render Shell (FASTEST)

1. Go to your Render dashboard: https://dashboard.render.com
2. Click your **koki-foodhub** service
3. Click **"Shell"** tab at the top
4. Run this command:

```bash
python manage.py loaddata export_products.json export_sales.json export_inventory.json
```

Wait for completion. You should see:
```
Installed 258 objects from 1 fixture
Installed 262 objects from 1 fixture
Installed 133 objects from 1 fixture
```

## Option 2: Use Manual Python Script

In Render Shell, run:
```bash
python import_render_data.py
```

## Verify the Import

After importing, visit:
- **Diagnostic Page**: https://koki-foodhub.onrender.com/forecast/debug/
- **Product Forecast**: https://koki-foodhub.onrender.com/product-forecast/

You should see your 258 products with forecasts and the Product Performance table showing:
- Product names (Double Cola, Wings, etc.)
- Categories
- Last 7 Days sales
- Last 30 Days sales
- Trends
- Predicted (Next 7D) values

## Troubleshooting

**If you see "Ignoring fixture ..."**
- The data may already be imported
- Or IDs might be conflicting
- Try clearing the database first:

```bash
# CAUTION: This deletes all data!
python manage.py flush --no-input
python manage.py migrate
python manage.py loaddata export_products.json export_sales.json export_inventory.json
```

**If forecast still shows 0**
- Run the diagnostic again: `/forecast/debug/`
- Check if products and sales count increased
- The forecast calculation needs data from the last 90 days

**Database URL issues**
- Ensure DATABASE_URL is set in Render environment variables
- Should be: `postgresql://user:pass@host/database`

---

**Questions?** Check `/forecast/debug/` for real-time database status.
