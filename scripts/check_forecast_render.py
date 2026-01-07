import os
import sys
import django
# ensure project root is on PYTHONPATH
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()
from django.test import Client
from django.contrib.auth import get_user_model
User = get_user_model()
# ensure a user exists and authenticate the client
user, _ = User.objects.get_or_create(username='test_local_user', defaults={'email':'local@example.com'})
user.set_unusable_password()
user.save()
c = Client()
c.force_login(user)
r = c.get('/forecast/')
s = r.content.decode('utf-8')
print('STATUS_CODE:', r.status_code)
print('HAS_FORECAST_HERO_GRID:', 'forecast-hero-grid' in s)
print('HAS_HERO_AMOUNT:', 'hero-amount' in s)
print('HAS_HERO_PCT:', 'hero-pct' in s)
print('STYLESHEET_REFERENCES (first 10 lines containing "stylesheet" or "styles.css"):\n')
for line in [l for l in s.splitlines() if 'stylesheet' in l or 'styles.css' in l][:10]:
    print(line)
print('\n---SNIPPET---\n')
start = s.find('<div class="forecast-hero-grid"')
if start != -1:
    print(s[start:start+800])
else:
    print('No forecast-hero-grid found')
