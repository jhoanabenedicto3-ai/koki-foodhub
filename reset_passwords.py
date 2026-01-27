#!/usr/bin/env python
"""
Reset user passwords to default 'password123'
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.contrib.auth.models import User

# Users to reset password for
users_to_reset = ['joanna', 'admin1', 'admin2']

for username in users_to_reset:
    try:
        user = User.objects.get(username=username)
        user.set_password('password123')
        user.save()
        print(f"✓ Reset {username} password to 'password123'")
    except User.DoesNotExist:
        print(f"✗ User {username} not found")

# Also make sure admin user has the right password
admin = User.objects.get(username='admin')
admin.set_password('admin123')
admin.save()
print(f"✓ Ensured admin password is 'admin123'")

print("\nDone! You can now login with:")
print("  - Username: admin, Password: admin123")
print("  - Username: joanna, Password: password123")
print("  - Username: admin1, Password: password123")
print("  - Username: admin2, Password: password123")
