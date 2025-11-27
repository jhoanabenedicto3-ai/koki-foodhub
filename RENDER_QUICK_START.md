# Deploying Koki's Foodhub to Render - Complete Steps

## Your GitHub Repository
- **Repository:** https://github.com/benedictojiro58-gif/koki-foodhub
- **Branch:** main

## ✅ What's Already Done
Your project is already configured for production deployment:
- ✅ `requirements.txt` - All Python dependencies
- ✅ `Procfile` - Render deployment config
- ✅ `runtime.txt` - Python 3.11.7
- ✅ `build.sh` - Build script
- ✅ `.gitignore` - Ignore sensitive files
- ✅ `settings.py` - Production settings configured
- ✅ Git repository initialized locally

## 🔐 GitHub Access Issue

You're getting a `403 Permission Denied` error because the local machine doesn't have GitHub authentication.

**Solution:** Push from a machine where you're logged into GitHub, or use GitHub CLI:

```bash
# Option 1: Using GitHub CLI (Recommended)
gh auth login
# Follow prompts to authenticate
git push -u origin main

# Option 2: Using Personal Access Token
# 1. Go to https://github.com/settings/tokens
# 2. Create new token with 'repo' scope
# 3. Use token as password when prompted
git push -u origin main
```

## 📋 Steps to Deploy on Render

### Step 1: Create PostgreSQL Database

1. Go to https://dashboard.render.com
2. Click **"New"** → **"PostgreSQL"**
3. Configure:
   - **Name:** `koki-foodhub-db`
   - **Database:** `koki_foodhub`
   - **User:** `koki_user`
   - **Region:** Choose closest to you
   - **PostgreSQL Version:** 15
4. Click **"Create Database"**
5. Save the connection string shown (you'll need it next)

### Step 2: Create Web Service

1. Go to https://dashboard.render.com
2. Click **"New"** → **"Web Service"**
3. Choose **"Deploy existing code from a repository"**
4. Click **"Connect" on GitHub** and authorize Render
5. Select `benedictojiro58-gif/koki-foodhub`
6. Configure:

   | Setting | Value |
   |---------|-------|
   | **Name** | `koki-foodhub` |
   | **Region** | Same as database |
   | **Branch** | `main` |
   | **Runtime** | `Python 3` |
   | **Build Command** | `pip install -r requirements.txt && python manage.py collectstatic --noinput` |
   | **Start Command** | `gunicorn koki_foodhub.wsgi` |

### Step 3: Add Environment Variables

Click **"Advanced"** and add these variables:

```
DEBUG=False
SECRET_KEY=[generate one using: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"]
ALLOWED_HOSTS=your-service-name.onrender.com

POSTGRES_NAME=koki_foodhub
POSTGRES_USER=koki_user
POSTGRES_PASSWORD=[password from database]
POSTGRES_HOST=[host from database connection string]
POSTGRES_PORT=5432
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Wait for build to complete (3-5 minutes)
3. Check "Logs" tab to verify success
4. Your app will be live at the URL shown (e.g., `https://koki-foodhub-xxxxx.onrender.com`)

## 📊 After Deployment

### Create Admin User

1. Go to your Web Service on Render
2. Click **"Shell"** tab
3. Run:
   ```bash
   python manage.py createsuperuser
   ```
4. Enter username, email, password
5. Access admin at: `https://your-app-url.com/admin`

### Database Migrations

Migrations run automatically via Procfile's `release` command. If needed manually:

1. In Render Shell: `python manage.py migrate`

## 🚀 Updating Your App

After making changes locally:

```bash
git add .
git commit -m "Your changes"
git push origin main
```

Render automatically redeploys when you push to main!

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Build fails** | Check Logs tab for error messages |
| **Database connection error** | Verify POSTGRES_* environment variables |
| **500 error on app** | Check Logs; run `python manage.py check` locally |
| **Static files not loading** | Ensure `python manage.py collectstatic` ran |
| **Can't push to GitHub** | Use GitHub CLI or personal access token for authentication |

## 📱 Your App Features

Once deployed, your Koki's Foodhub restaurant system will have:

✅ Dashboard with product search
✅ Transaction cart
✅ Sales tracking
✅ Inventory management
✅ Forecast predictions
✅ Admin interface
✅ User authentication
✅ PostgreSQL database

---

**Ready to deploy?** Follow the steps above and your app will be live in minutes! 🎉
