#!/usr/bin/env python3
"""
Koki's Foodhub - Render Deployment Helper
Automates local preparation for fresh Render deployment
"""

import os
import sys
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")


def print_step(num, text):
    """Print step number"""
    print(f"\n📋 STEP {num}: {text}")
    print(f"{'─'*60}")


def generate_secret_key():
    """Generate Django secret key"""
    from django.core.management.utils import get_random_secret_key
    return get_random_secret_key()


def main():
    print_header("🚀 KOKI'S FOODHUB - RENDER DEPLOYMENT HELPER")
    
    print("""
This helper will prepare everything for fresh deployment to Render.
You'll still need to do the Render steps manually (clicking buttons),
but this prepares everything locally.
    """)

    # STEP 1: Generate SECRET_KEY
    print_step(1, "GENERATE SECRET_KEY")
    try:
        secret_key = generate_secret_key()
        print(f"✅ Generated SECRET_KEY:")
        print(f"\n   {secret_key}\n")
        print("📋 COPY THIS! You'll need it in Render environment variables.")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

    # STEP 2: Check requirements.txt
    print_step(2, "VERIFY REQUIREMENTS.TXT")
    req_file = Path("requirements.txt")
    if req_file.exists():
        with open(req_file) as f:
            packages = f.readlines()
        print(f"✅ requirements.txt found with {len(packages)} packages:")
        for pkg in packages[:5]:
            print(f"   - {pkg.strip()}")
        if len(packages) > 5:
            print(f"   ... and {len(packages) - 5} more")
    else:
        print("❌ requirements.txt not found!")
        sys.exit(1)

    # STEP 3: Check Procfile
    print_step(3, "VERIFY PROCFILE")
    procfile = Path("Procfile")
    if procfile.exists():
        with open(procfile) as f:
            content = f.read()
        print("✅ Procfile configured:")
        for line in content.strip().split('\n'):
            print(f"   {line}")
    else:
        print("❌ Procfile not found!")
        sys.exit(1)

    # STEP 4: Check settings.py
    print_step(4, "VERIFY DJANGO SETTINGS")
    settings_file = Path("koki_foodhub/settings.py")
    if settings_file.exists():
        with open(settings_file) as f:
            content = f.read()
        checks = {
            "DEBUG": "DEBUG = os.getenv" in content,
            "DATABASE_URL": "DATABASE_URL = os.getenv" in content,
            "ALLOWED_HOSTS": "ALLOWED_HOSTS = os.getenv" in content,
            "WhiteNoise": "whitenoise.middleware.WhiteNoiseMiddleware" in content,
        }
        print("✅ Settings configuration:")
        for check, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check}")
    else:
        print("❌ settings.py not found!")
        sys.exit(1)

    # STEP 5: Check init_render command
    print_step(5, "VERIFY INIT_RENDER COMMAND")
    init_file = Path("core/management/commands/init_render.py")
    if init_file.exists():
        print("✅ init_render.py management command found")
        print("   This will auto-create admin user on Render")
    else:
        print("❌ init_render.py not found!")
        sys.exit(1)

    # STEP 6: Check Git status
    print_step(6, "VERIFY GIT STATUS")
    try:
        from subprocess import run, PIPE
        result = run(["git", "status", "--short"], capture_output=True, text=True)
        if result.returncode == 0:
            uncommitted = result.stdout.strip()
            if uncommitted:
                print(f"⚠️  Uncommitted changes found:")
                for line in uncommitted.split('\n')[:5]:
                    print(f"   {line}")
                print(f"\n📝 Recommended: Commit these changes before deploying")
                response = input("   Do you want to commit now? (y/n): ").lower()
                if response == 'y':
                    run(["git", "add", "."])
                    run(["git", "commit", "-m", "Pre-deployment: Final code updates"])
                    run(["git", "push", "origin", "main"])
                    print("✅ Changes committed and pushed")
            else:
                print("✅ Everything committed (clean working directory)")
        else:
            print("⚠️  Could not check git status")
    except Exception as e:
        print(f"⚠️  Git check skipped: {e}")

    # STEP 7: Create deployment guide
    print_step(7, "RENDER MANUAL STEPS")
    print("""
Now go to Render.com and do these 7 steps manually:

1️⃣  CLEAN UP (optional but recommended)
   - Delete old web service from https://render.com/dashboard
   - Delete old database from https://render.com/dashboard

2️⃣  CREATE DATABASE
   - Go to https://render.com/dashboard
   - Click "+ New" → "PostgreSQL"
   - Name: koki-foodhub-db
   - User: koki_user
   - Region: Oregon
   - Plan: Free
   - Click "Create Database"
   - 📋 SAVE the "Internal Database URL"

3️⃣  CREATE WEB SERVICE
   - Click "+ New" → "Web Service"
   - Connect GitHub (koki-foodhub repo)
   - Service Name: koki-foodhub
   - Region: Same as database
   - Plan: Free

4️⃣  SET BUILD & START COMMANDS
   Build: pip install -r requirements.txt && python manage.py collectstatic --noinput
   Start: gunicorn koki_foodhub.wsgi
   Click "Advanced"

5️⃣  ADD ENVIRONMENT VARIABLES (CRITICAL!)
   DEBUG = False
   SECRET_KEY = """ + secret_key + """
   DATABASE_URL = [paste PostgreSQL Internal URL from Step 2]
   ALLOWED_HOSTS = koki-foodhub.onrender.com
   ADMIN_PASSWORD = [create a strong password]
   
   Click "Save"

6️⃣  WAIT FOR BUILD (3-5 minutes)
   - Watch "Logs" tab
   - Look for "Your service is live"
   - Don't close the dashboard

7️⃣  TEST YOUR APP
   - Go to: https://koki-foodhub.onrender.com
   - Login: admin / [your ADMIN_PASSWORD]
   - Test dashboard features
    """)

    print_header("✅ LOCAL PREPARATION COMPLETE")
    print("""
Your code is ready for Render deployment!

Next steps:
1. Go to https://render.com/dashboard
2. Follow the 7 manual steps above
3. Email me if you hit any issues!

Your SECRET_KEY (save for Step 5):
""")
    print(f"   {secret_key}")


if __name__ == "__main__":
    main()
