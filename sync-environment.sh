#!/bin/bash
# ENVIRONMENT SYNCHRONIZATION SCRIPT
# This script ensures localhost development environment matches production

set -e

echo "================================"
echo "KOKI'S FOODHUB - ENVIRONMENT SYNC"
echo "================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Check Python Version
echo "1️⃣  Checking Python Version..."
PYTHON_VERSION=$(python --version 2>&1 | grep -oP 'Python \K[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.11"

if [[ "$PYTHON_VERSION" == "$REQUIRED_VERSION"* ]]; then
    echo -e "${GREEN}✓${NC} Python version $PYTHON_VERSION matches (required: 3.11.x)"
else
    echo -e "${RED}✗${NC} Python version mismatch. Have: $PYTHON_VERSION, Need: 3.11.x"
    echo "  Install Python 3.11 from python.org or your package manager"
    exit 1
fi
echo ""

# 2. Check Virtual Environment
echo "2️⃣  Checking Virtual Environment..."
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo -e "${YELLOW}⚠${NC} Virtual environment not activated"
    echo "  Run: source .venv/Scripts/activate"
    exit 1
else
    echo -e "${GREEN}✓${NC} Virtual environment activated: $VIRTUAL_ENV"
fi
echo ""

# 3. Check .env.local
echo "3️⃣  Checking .env.local Configuration..."
if [[ ! -f ".env.local" ]]; then
    echo -e "${YELLOW}⚠${NC} .env.local not found, creating from template..."
    cat > .env.local << 'EOF'
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
EOF
    echo -e "${GREEN}✓${NC} Created .env.local with development defaults"
else
    echo -e "${GREEN}✓${NC} .env.local exists"
    # Verify key settings
    if grep -q "DEBUG=True" .env.local; then
        echo -e "  ${GREEN}✓${NC} DEBUG=True (development mode)"
    else
        echo -e "  ${RED}✗${NC} DEBUG should be True for localhost"
    fi
    
    if grep -q "USE_DOTENV=true" .env.local; then
        echo -e "  ${GREEN}✓${NC} USE_DOTENV=true (environment loading enabled)"
    fi
    
    if grep -q "sqlite" .env.local; then
        echo -e "  ${GREEN}✓${NC} Using SQLite database"
    else
        echo -e "  ${YELLOW}⚠${NC} Not using SQLite - may cause issues"
    fi
fi
echo ""

# 4. Install Dependencies
echo "4️⃣  Installing/Verifying Dependencies..."
pip install -q -r requirements.txt 2>/dev/null
echo -e "${GREEN}✓${NC} All dependencies installed"

# Verify key versions
echo "  Checking versions:"
DJANGO_VER=$(pip show django | grep Version | cut -d' ' -f2)
echo -e "  ${GREEN}✓${NC} Django: $DJANGO_VER (required: 5.2.6)"

PYTHON_DOTENV_VER=$(pip show python-dotenv | grep Version | cut -d' ' -f2)
echo -e "  ${GREEN}✓${NC} python-dotenv: $PYTHON_DOTENV_VER"
echo ""

# 5. Database Setup
echo "5️⃣  Setting Up Database..."
if [[ ! -f "db.sqlite3" ]]; then
    echo -e "  ${YELLOW}⚠${NC} db.sqlite3 not found, creating..."
fi

echo "  Running migrations..."
python manage.py migrate --quiet
echo -e "${GREEN}✓${NC} Database migrations applied"
echo ""

# 6. Create Admin User
echo "6️⃣  Checking Admin User..."
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
echo ""

# 7. Load Sample Data
echo "7️⃣  Loading Sample Data..."
FIXTURES=0
for fixture in export_products.json export_sales.json export_inventory.json recent_sales.json; do
    if [[ -f "$fixture" ]]; then
        python manage.py loaddata "$fixture" --quiet 2>/dev/null && ((FIXTURES++))
    fi
done

if [[ $FIXTURES -gt 0 ]]; then
    echo -e "${GREEN}✓${NC} Loaded $FIXTURES data fixtures"
else
    echo -e "${YELLOW}⚠${NC} No sample data found (optional)"
fi
echo ""

# 8. Collect Static Files
echo "8️⃣  Collecting Static Files..."
python manage.py collectstatic --noinput --quiet 2>/dev/null
echo -e "${GREEN}✓${NC} Static files collected"
echo ""

# 9. Verify Configuration
echo "9️⃣  Verifying Configuration..."
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
echo ""

# 10. Summary
echo "================================"
echo -e "${GREEN}✓ ENVIRONMENT SETUP COMPLETE${NC}"
echo "================================"
echo ""
echo "To start development:"
echo "  1. Activate environment: source .venv/Scripts/activate"
echo "  2. Run server: python manage.py runserver"
echo "  3. Visit: http://localhost:8000"
echo "  4. Login: admin / admin123"
echo ""
echo "To verify alignment with production:"
echo "  - Test discount features (Senior, PWD, Student presets)"
echo "  - Test custom percent and peso discounts"
echo "  - Verify calculations and receipt output"
echo "  - Compare with https://koki-foodhub.onrender.com"
echo ""
