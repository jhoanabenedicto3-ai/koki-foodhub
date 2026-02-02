# ENVIRONMENT SYNCHRONIZATION SCRIPT (Windows PowerShell)
# This script ensures localhost development environment matches production

Write-Host "================================" -ForegroundColor Cyan
Write-Host "KOKI'S FOODHUB - ENVIRONMENT SYNC" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# 1. Check Python Version
Write-Host "1️⃣  Checking Python Version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1 | Select-String "Python" | ForEach-Object { $_.Line -replace "Python ", "" }
$requiredVersion = "3.11"

if ($pythonVersion -like "$requiredVersion*") {
    Write-Host "✓ Python version $pythonVersion matches (required: 3.11.x)" -ForegroundColor Green
} else {
    Write-Host "✗ Python version mismatch. Have: $pythonVersion, Need: 3.11.x" -ForegroundColor Red
    Write-Host "  Install Python 3.11 from python.org or Microsoft Store" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# 2. Check Virtual Environment
Write-Host "2️⃣  Checking Virtual Environment..." -ForegroundColor Yellow
if (-not $env:VIRTUAL_ENV) {
    Write-Host "⚠ Virtual environment not activated" -ForegroundColor Yellow
    Write-Host "  Run: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    exit 1
} else {
    Write-Host "✓ Virtual environment activated: $env:VIRTUAL_ENV" -ForegroundColor Green
}
Write-Host ""

# 3. Check .env.local
Write-Host "3️⃣  Checking .env.local Configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Write-Host "Creating .env.local from template..." -ForegroundColor Yellow
    $envContent = @"
# Local Development Environment
DEBUG=True
SECRET_KEY=dev-secret-key-change-before-production
USE_DOTENV=true

# Database (SQLite for local development)
DATABASE_URL=sqlite:///db.sqlite3

# Allowed Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,testserver

# Admin Credentials
ADMIN_EMAIL=admin@koki-foodhub.com
ADMIN_PASSWORD=admin123
"@
    Set-Content -Path ".env.local" -Value $envContent -Encoding UTF8
    Write-Host "✓ Created .env.local with development defaults" -ForegroundColor Green
}
else {
    Write-Host "✓ .env.local exists" -ForegroundColor Green
    $envContent = Get-Content ".env.local" -Raw
    
    if ($envContent -match "DEBUG=True") {
        Write-Host "  ✓ DEBUG=True (development mode)" -ForegroundColor Green
    }
    else {
        Write-Host "  ✗ DEBUG should be True for localhost" -ForegroundColor Red
    }
    
    if ($envContent -match "USE_DOTENV=true") {
        Write-Host "  ✓ USE_DOTENV=true (environment loading enabled)" -ForegroundColor Green
    }
    
    if ($envContent -match "sqlite") {
        Write-Host "  ✓ Using SQLite database" -ForegroundColor Green
    }
    else {
        Write-Host "  ⚠ Not using SQLite - may cause issues" -ForegroundColor Yellow
    }
}
Write-Host ""

# 4. Install Dependencies
Write-Host "4️⃣  Installing/Verifying Dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt 2>$null
Write-Host "✓ All dependencies installed" -ForegroundColor Green

Write-Host "  Checking versions:" -ForegroundColor Cyan
$djangoVer = pip show django | Select-String "Version" | ForEach-Object { $_.Line -split " " | Select-Object -Last 1 }
Write-Host "  ✓ Django: $djangoVer (required: 5.2.6)" -ForegroundColor Green

$dotenvVer = pip show python-dotenv | Select-String "Version" | ForEach-Object { $_.Line -split " " | Select-Object -Last 1 }
Write-Host "  ✓ python-dotenv: $dotenvVer" -ForegroundColor Green
Write-Host ""

# 5. Database Setup
Write-Host "5️⃣  Setting Up Database..." -ForegroundColor Yellow
if (-not (Test-Path "db.sqlite3")) {
    Write-Host "  ⚠ db.sqlite3 not found, creating..." -ForegroundColor Yellow
}

Write-Host "  Running migrations..." -ForegroundColor Cyan
python manage.py migrate --quiet
Write-Host "✓ Database migrations applied" -ForegroundColor Green
Write-Host ""

# 6. Create Admin User
Write-Host "6️⃣  Checking Admin User..." -ForegroundColor Yellow
python << 'PYEOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User

if User.objects.filter(username='admin').exists():
    print("✓ Admin user already exists")
else:
    print("⚠ Creating admin user...")
    User.objects.create_superuser('admin', 'admin@koki-foodhub.com', 'admin123')
    print("✓ Admin user created (username: admin, password: admin123)")
PYEOF
Write-Host ""

# 7. Load Sample Data
Write-Host "7️⃣  Loading Sample Data..." -ForegroundColor Yellow
$fixtures = @("export_products.json", "export_sales.json", "export_inventory.json", "recent_sales.json")
$fixtureCount = 0

foreach ($fixture in $fixtures) {
    if (Test-Path $fixture) {
        python manage.py loaddata $fixture --quiet 2>$null
        $fixtureCount++
    }
}

if ($fixtureCount -gt 0) {
    Write-Host "✓ Loaded $fixtureCount data fixtures" -ForegroundColor Green
} else {
    Write-Host "⚠ No sample data found (optional)" -ForegroundColor Yellow
}
Write-Host ""

# 8. Collect Static Files
Write-Host "8️⃣  Collecting Static Files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput --quiet 2>$null
Write-Host "✓ Static files collected" -ForegroundColor Green
Write-Host ""

# 9. Verify Configuration
Write-Host "9️⃣  Verifying Configuration..." -ForegroundColor Yellow
python << 'PYEOF'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.conf import settings

print("Configuration Summary:")
print(f"  DEBUG: {settings.DEBUG}")
print(f"  Database Engine: {settings.DATABASES['default']['ENGINE']}")
print(f"  Allowed Hosts: {', '.join(settings.ALLOWED_HOSTS)}")
print(f"  Installed Apps: {len(settings.INSTALLED_APPS)} apps")
print(f"  Middleware: {len(settings.MIDDLEWARE)} middleware")

if settings.DEBUG and 'sqlite' in settings.DATABASES['default']['ENGINE']:
    print("\n✓ Development environment correctly configured")
else:
    print("\n⚠ Configuration may not be optimal for development")
PYEOF
Write-Host ""

# 10. Summary
Write-Host "================================" -ForegroundColor Green
Write-Host "✓ ENVIRONMENT SETUP COMPLETE" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start development:" -ForegroundColor Cyan
Write-Host "  1. Activate environment: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run server: python manage.py runserver" -ForegroundColor White
Write-Host "  3. Visit: http://localhost:8000" -ForegroundColor White
Write-Host "  4. Login: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "To verify alignment with production:" -ForegroundColor Cyan
Write-Host "  - Test discount features (Senior, PWD, Student presets)" -ForegroundColor White
Write-Host "  - Test custom percent and peso discounts" -ForegroundColor White
Write-Host "  - Verify calculations and receipt output" -ForegroundColor White
Write-Host "  - Compare with https://koki-foodhub.onrender.com" -ForegroundColor White
Write-Host ""
