# ENVIRONMENT ALIGNMENT VERIFICATION CHECKLIST

## Current Status: Ready for Alignment

This checklist ensures your localhost development environment is 100% aligned with production.

---

## ✅ QUICK SETUP (5 Minutes)

### Step 1: Activate Virtual Environment
```powershell
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

### Step 2: Verify .env.local Exists
```powershell
# Check if file exists
Test-Path ".env.local"
# Should output: True

# If False, create it with:
@"
DEBUG=True
SECRET_KEY=dev-secret-key-change-before-production
USE_DOTENV=true
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
ADMIN_EMAIL=admin@koki-foodhub.com
ADMIN_PASSWORD=admin123
"@ | Out-File -Encoding utf8 ".env.local"
```

### Step 3: Run Sync Script
```powershell
# Windows (from repository root)
powershell -ExecutionPolicy Bypass -File sync-environment.ps1

# macOS/Linux
bash sync-environment.sh
```

This script will:
- ✓ Check Python version (3.11.x)
- ✓ Verify virtual environment
- ✓ Create .env.local if needed
- ✓ Install dependencies
- ✓ Run migrations
- ✓ Create admin user
- ✓ Load sample data
- ✓ Collect static files

---

## 🔍 DETAILED VERIFICATION CHECKLIST

### Configuration

- [ ] **Python Version**
  ```powershell
  python --version
  # Should show: Python 3.11.x
  ```

- [ ] **.env.local File**
  ```powershell
  Get-Content ".env.local"
  # Should show all required variables
  ```

- [ ] **DEBUG Mode (Development)**
  ```powershell
  grep DEBUG .env.local
  # Should show: DEBUG=True
  ```

- [ ] **Database Type (SQLite)**
  ```powershell
  grep DATABASE_URL .env.local
  # Should show: DATABASE_URL=sqlite:///db.sqlite3
  ```

### Dependencies

- [ ] **Django Version**
  ```powershell
  pip show django | grep Version
  # Should show: Version: 5.2.6
  ```

- [ ] **Python-dotenv Installed**
  ```powershell
  pip show python-dotenv
  # Should show: Version: 1.0.0
  ```

- [ ] **All Requirements Met**
  ```powershell
  pip check
  # Should show: No broken requirements found.
  ```

### Database

- [ ] **Migrations Applied**
  ```powershell
  python manage.py showmigrations | grep "\[X\]"
  # Should show multiple [X] marks (migrations completed)
  ```

- [ ] **Database File Exists**
  ```powershell
  Test-Path "db.sqlite3"
  # Should output: True
  ```

- [ ] **Admin User Exists**
  ```powershell
  python manage.py shell
  >>> from django.contrib.auth.models import User
  >>> User.objects.filter(username='admin').exists()
  # Should return: True
  ```

### Sample Data

- [ ] **Products Loaded**
  ```powershell
  python manage.py shell
  >>> from core.models import Product
  >>> Product.objects.count()
  # Should return: > 0
  ```

- [ ] **Sales Data Loaded**
  ```powershell
  python manage.py shell
  >>> from core.models import Sale
  >>> Sale.objects.count()
  # Should return: > 0
  ```

### Static Files

- [ ] **Static Files Collected**
  ```powershell
  Test-Path "staticfiles"
  # Should output: True
  ```

- [ ] **CSS/JS Files Present**
  ```powershell
  Get-ChildItem "staticfiles" -Recurse | Measure-Object
  # Should show: Count > 100 (many files)
  ```

---

## 🏃 QUICK START (After Setup)

### Start Development Server
```powershell
# From repository root with venv activated
python manage.py runserver

# Should output:
# Starting development server at http://127.0.0.1:8000/
# Quit the server with CONTROL-C.
```

### Access Application
```
URL: http://localhost:8000
Username: admin
Password: admin123
```

### Test Discount Feature
1. Login to dashboard
2. Add items to cart
3. Test Senior preset → Should apply 20% discount
4. Test PWD preset → Should apply 20% discount
5. Test Student preset → Should apply 5% discount
6. Test custom percent → Enter 15% → Should calculate correctly
7. Test custom peso → Enter ₱250 → Should show ₱250 off
8. Test validation → Enter 150% → Should show error
9. Print receipt → Should show discount details

---

## 🔄 SYNCHRONIZATION POINTS

### What's Automatically Aligned

✅ **Django Settings** (`settings.py`)
- Same models (Product, Sale, InventoryItem)
- Same middleware stack
- Same authentication backend
- Same security middleware
- Auto-switches database based on DEBUG flag

✅ **HTML/CSS/JavaScript** (`core/templates/`)
- Identical UI code
- Same discount logic in JavaScript
- Same validation rules
- Same form behavior
- Identical to production

✅ **API Endpoints** (`core/urls.py`)
- Same request/response structure
- Same error handling
- Same validation
- Same HTTP status codes

✅ **Database Schema** (`core/models.py`)
- Same models everywhere
- Same fields
- Same relationships
- Same validation rules

### What Requires Configuration

⚙️ **Environment Variables** (`.env.local`)
- Set `DEBUG=True` for development
- Set `DATABASE_URL=sqlite:///db.sqlite3`
- Keep other values consistent

⚙️ **Database Connection**
- Localhost: SQLite (automatic)
- Production: PostgreSQL (managed by Render)
- No code changes needed

⚙️ **Admin User**
- Localhost: Create with credentials of choice
- Production: Created by Render on startup
- Use `admin/admin123` for consistency

---

## 🧪 TESTING PARITY

### Test 1: Senior Citizen Discount

**Localhost:**
1. Add items (subtotal ₱1,000)
2. Click "Senior" preset
3. Verify: Shows "20% Off - Senior Citizen"
4. Verify: Discount amount = ₱200
5. Verify: Total = ₱800

**Production:**
1. Add items (subtotal ₱1,000)
2. Click "Senior" preset
3. Verify: Shows "20% Off - Senior Citizen"
4. Verify: Discount amount = ₱200
5. Verify: Total = ₱800

**Result:** ✅ Should be identical

### Test 2: Custom Peso Discount

**Localhost & Production (same steps):**
1. Add items (subtotal ₱2,000)
2. Toggle to "₱ Pesos"
3. Enter: 500
4. Enter reason: "Employee"
5. Verify: Shows "₱500.00 Off - Employee"
6. Verify: Total = ₱1,500
7. Print receipt
8. Verify: Receipt shows discount type and reason

**Result:** ✅ Should be identical

### Test 3: Validation

**Test:** Enter 150% discount
- Localhost: Shows error "Discount cannot exceed 100%"
- Production: Shows error "Discount cannot exceed 100%"
- Result: ✅ Identical

**Test:** Enter ₱3000 on ₱2000 subtotal
- Localhost: Shows error "₱ Discount cannot exceed subtotal..."
- Production: Shows error "₱ Discount cannot exceed subtotal..."
- Result: ✅ Identical

---

## 🛠️ TROUBLESHOOTING

### Issue: "ModuleNotFoundError: No module named 'django'"
**Solution:**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Issue: "OperationalError: no such table"
**Solution:**
```powershell
# Run migrations
python manage.py migrate
```

### Issue: "FileNotFoundError: db.sqlite3"
**Solution:**
```powershell
# Create database
python manage.py migrate
```

### Issue: "No such file or directory: '.env.local'"
**Solution:**
```powershell
# Create .env.local with required settings
# (See Quick Setup above or run sync script)
```

### Issue: "Admin user does not exist"
**Solution:**
```powershell
# Create admin user
python manage.py createsuperuser

# Or use auto-creation in sync script
```

### Issue: "Discount calculations differ from production"
**Solution:**
1. Check .env.local: `DEBUG=True` and `DATABASE_URL=sqlite:///db.sqlite3`
2. Verify Django version: `pip show django`
3. Check discount logic is identical in JavaScript
4. Clear browser cache (Ctrl+Shift+Del or Cmd+Shift+Del)
5. Run sync script to reset environment

---

## 📊 Configuration Comparison

| Setting | Localhost | Production | Note |
|---------|-----------|-----------|------|
| DEBUG | True | False | Auto-switches |
| Database | SQLite | PostgreSQL | Auto-switches |
| HTTPS | No | Yes | Auto-switches |
| SECRET_KEY | Dev key | Render-managed | Different per env |
| ALLOWED_HOSTS | localhost | .onrender.com | Environment-specific |
| Admin User | Manual/admin123 | Render auto-created | Same credentials for testing |
| Static Files | Auto-served | WhiteNoise + CDN | Different deployment |
| Logging | Console | Render logs | Different output location |

---

## ✅ FINAL CHECKLIST

Before deploying code changes, verify:

- [ ] Localhost runs without errors: `python manage.py runserver`
- [ ] All tests pass on localhost
- [ ] Discount feature works identically to production
- [ ] Admin login works: admin/admin123
- [ ] Sample data loads correctly
- [ ] Static files display properly
- [ ] Database migrations apply cleanly
- [ ] No Python version mismatches
- [ ] All dependencies match requirements.txt
- [ ] .env.local has correct settings

---

## 🚀 NEXT STEPS

1. **Run sync script** to automatically set up everything
2. **Test discount features** on localhost
3. **Compare behavior** with production
4. **Make code changes** with confidence that localhost matches production
5. **Commit changes** to git
6. **Push to GitHub** to auto-deploy to Render

---

## 📞 SUPPORT

If you encounter issues:
1. Check the **Troubleshooting** section above
2. Run the **sync script** to reset environment
3. Verify **Quick Setup** steps were followed
4. Check Django logs: `python manage.py runserver --verbosity 2`
5. Check database: `python manage.py dbshell`

---

**Status:** ✅ READY FOR DEVELOPMENT
**Last Updated:** February 2, 2026
**Framework:** Django 5.2.6
**Python:** 3.11.x
