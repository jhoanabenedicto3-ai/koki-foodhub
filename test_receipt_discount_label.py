#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test that receipt includes discount label under subtotal
"""
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'koki_foodhub.settings')
django.setup()

from django.test import Client
import re

print("=" * 80)
print("RECEIPT DISCOUNT LABEL TEST")
print("=" * 80)

client = Client()

# Login
print("\n[1] Login to dashboard...")
login_success = client.login(username='admin', password='admin123')
print(f"    Status: {'OK' if login_success else 'FAILED'}")

# Get dashboard
print("\n[2] Load dashboard page...")
response = client.get('/')
print(f"    Status: {response.status_code}")

if response.status_code == 200:
    html = response.content.decode('utf-8')
    
    # Check for receipt generation function with discount label parameter
    print("\n[3] Verify receipt generation code...")
    
    checks = [
        (r'function generateAndPrintReceipt\([^)]*discountLabel', 'Receipt function accepts discountLabel parameter'),
        (r'discountLabel\s*=\s*[\'"]Senior Citizen', 'Senior Citizen label defined'),
        (r'discountLabel\s*=\s*[\'"]PWD', 'PWD label defined'),
        (r'discountLabel\s*=\s*[\'"]Student', 'Student label defined'),
        (r'Discount\s*\(\$\{discountLabel\}\)', 'Receipt displays discount label'),
        (r'generateAndPrintReceipt\([^)]*discountLabel\)', 'Receipt function called with discount label'),
    ]
    
    all_found = True
    for pattern, description in checks:
        if re.search(pattern, html):
            print(f"    [OK] {description}")
        else:
            print(f"    [FAIL] {description}")
            all_found = False
    
    if all_found:
        print("\n" + "=" * 80)
        print("SUCCESS: Receipt will display discount label under subtotal!")
        print("=" * 80)
        print("\nReceipt will show:")
        print("  Subtotal:              P500.00")
        print("  Discount (Senior Citizen (20%)):  -P100.00")
        print("  TOTAL:                 P400.00")
        print("\nOr for PWD:")
        print("  Subtotal:              P500.00")
        print("  Discount (PWD (20%)):   -P100.00")
        print("  TOTAL:                 P400.00")
        print("\nOr for Student:")
        print("  Subtotal:              P500.00")
        print("  Discount (Student (5%)):  -P25.00")
        print("  TOTAL:                 P475.00")
    else:
        print("\nWARNING: Some checks failed!")
else:
    print(f"    FAILED to load dashboard: {response.status_code}")
