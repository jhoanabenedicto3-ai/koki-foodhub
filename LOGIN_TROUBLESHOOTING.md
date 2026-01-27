# LOGIN TROUBLESHOOTING GUIDE

## Quick Test - Verified Working Credentials

Try logging in with these credentials (tested and working):

```
Username: admin
Password: admin123
```

Or:

```
Username: joanna
Password: password123
```

## If Login Still Doesn't Work

### Step 1: Clear Browser Cache & Cookies
1. Open your browser DevTools (F12)
2. Go to Application > Cookies > Delete all cookies for `127.0.0.1:8000`
3. Go to Application > Storage > Clear Site Data
4. Hard refresh the page (Ctrl+Shift+R)

### Step 2: Check Your Browser Console for Errors
1. Open DevTools (F12)
2. Go to Console tab
3. Look for any red error messages
4. Screenshot any errors and report them

### Step 3: Test the Debug Endpoint
1. After logging in, go to: `http://127.0.0.1:8000/api/debug/status/`
2. You should see JSON showing:
   - `"authenticated": true`
   - `"username": "admin"` (or your username)
   - This proves the session is working

### Step 4: Check if Dashboard is Loading
1. After login, you should be redirected to `/` (home/dashboard)
2. The page should show products and inventory
3. If the page is blank or shows errors, check the browser console (Step 2)

## What to Check

### Browser Requirements
- ✓ JavaScript must be enabled
- ✓ Cookies must be enabled
- ✓ SessionID cookie should appear after login

### Django Backend
- ✓ Database is accessible (check terminal for errors)
- ✓ All migrations are applied
- ✓ Static files are served properly

## If Dashboard Shows But is Blank/Broken

This usually means:
1. CSS is not loading - check if `/static/styles.css` returns 200
2. JavaScript error - check browser console (F12 > Console)
3. Data not loading - check browser Network tab (F12 > Network)

## Nuclear Option: Reset Everything

If nothing works, try:

```bash
# 1. Clear database sessions
python manage.py shell -c "from django.contrib.sessions.models import Session; Session.objects.all().delete()"

# 2. Clear browser cookies (already done above)

# 3. Restart Django server:
# Kill the current `runserver` process
# Run: python manage.py runserver
```

## Report Issues

If you still can't login, please provide:
1. Browser console errors (F12 > Console)
2. Network tab failures (F12 > Network) 
3. Any error messages displayed
4. Output of debug endpoint: `http://127.0.0.1:8000/api/debug/status/`
