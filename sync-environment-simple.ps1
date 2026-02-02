# ENVIRONMENT SYNCHRONIZATION SCRIPT (Windows PowerShell) - Simplified
# This script ensures localhost development environment matches production

Write-Host "================================" -ForegroundColor Cyan
Write-Host "KOKI'S FOODHUB - ENVIRONMENT SYNC" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Create .env.local if needed
Write-Host "1. Checking .env.local..." -ForegroundColor Yellow
if (-not (Test-Path ".env.local")) {
    Write-Host "   Creating .env.local..." -ForegroundColor Yellow
    $envContent = @"
# Local Development Environment
DEBUG=True
SECRET_KEY=dev-secret-key-change-before-production
USE_DOTENV=true
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
ADMIN_EMAIL=admin@koki-foodhub.com
ADMIN_PASSWORD=admin123
"@
    Set-Content -Path ".env.local" -Value $envContent -Encoding UTF8
    Write-Host "   ✓ Created .env.local" -ForegroundColor Green
}
else {
    Write-Host "   ✓ .env.local exists" -ForegroundColor Green
}
Write-Host ""

# Step 2: Install dependencies
Write-Host "2. Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt 2>$null
Write-Host "   ✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 3: Run migrations
Write-Host "3. Running database migrations..." -ForegroundColor Yellow
python manage.py migrate --quiet 2>$null
Write-Host "   ✓ Migrations applied" -ForegroundColor Green
Write-Host ""

# Step 4: Create admin user if needed
Write-Host "4. Checking admin user..." -ForegroundColor Yellow
python -c "import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings'); django.setup(); from django.contrib.auth.models import User; User.objects.get_or_create(username='admin', defaults={'email': 'admin@koki-foodhub.com', 'is_staff': True, 'is_superuser': True})" 2>$null
python -c "import os; import django; os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings'); django.setup(); from django.contrib.auth.models import User; u = User.objects.get(username='admin'); u.set_password('admin123'); u.save()" 2>$null
Write-Host "   ✓ Admin user ready (admin/admin123)" -ForegroundColor Green
Write-Host ""

# Step 5: Load sample data
Write-Host "5. Loading sample data..." -ForegroundColor Yellow
$fixtures = @("export_products.json", "export_sales.json", "export_inventory.json", "recent_sales.json")
$count = 0
foreach ($fixture in $fixtures) {
    if (Test-Path $fixture) {
        python manage.py loaddata $fixture --quiet 2>$null
        $count++
    }
}
if ($count -gt 0) {
    Write-Host "   ✓ Loaded $count data fixtures" -ForegroundColor Green
}
else {
    Write-Host "   ⚠ No sample data found (optional)" -ForegroundColor Yellow
}
Write-Host ""

# Step 6: Collect static files
Write-Host "6. Collecting static files..." -ForegroundColor Yellow
python manage.py collectstatic --noinput --quiet 2>$null
Write-Host "   ✓ Static files collected" -ForegroundColor Green
Write-Host ""

# Summary
Write-Host "================================" -ForegroundColor Green
Write-Host "✓ ENVIRONMENT SETUP COMPLETE" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start development:" -ForegroundColor Cyan
Write-Host "  1. python manage.py runserver" -ForegroundColor White
Write-Host "  2. Visit http://localhost:8000" -ForegroundColor White
Write-Host "  3. Login: admin / admin123" -ForegroundColor White
Write-Host ""
Write-Host "To verify alignment with production:" -ForegroundColor Cyan
Write-Host "  - Test Senior/PWD/Student presets" -ForegroundColor White
Write-Host "  - Test custom percent and peso discounts" -ForegroundColor White
Write-Host "  - Compare calculations with production" -ForegroundColor White
Write-Host "  - Verify receipt output matches" -ForegroundColor White
Write-Host ""
