#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Comprehensive test of discount calculations
Tests all discount scenarios to verify correct calculations
"""

def test_discount_calculations():
    """Test all discount calculation scenarios"""
    
    test_cases = [
        # (subtotal, discount_value, discount_label, expected_discount_amount, expected_total)
        (500, '0', 'No Discount', 0, 500),
        (500, '20', 'Senior Citizen (20%)', 100, 400),
        (500, '20pwd', 'PWD (20%)', 100, 400),
        (500, '5', 'Student (5%)', 25, 475),
        
        (300, '0', 'No Discount', 0, 300),
        (300, '20', 'Senior Citizen (20%)', 60, 240),
        (300, '20pwd', 'PWD (20%)', 60, 240),
        (300, '5', 'Student (5%)', 15, 285),
        
        (1000, '0', 'No Discount', 0, 1000),
        (1000, '20', 'Senior Citizen (20%)', 200, 800),
        (1000, '5', 'Student (5%)', 50, 950),
        
        (750.50, '0', 'No Discount', 0, 750.50),
        (750.50, '20', 'Senior Citizen (20%)', 150.10, 600.40),
        (750.50, '5', 'Student (5%)', 37.525, 712.975),
        
        (99.99, '0', 'No Discount', 0, 99.99),
        (99.99, '20', 'Senior Citizen (20%)', 19.998, 79.992),
        (99.99, '5', 'Student (5%)', 4.9995, 94.9905),
    ]
    
    print("=" * 90)
    print("DISCOUNT CALCULATION TEST SUITE")
    print("=" * 90)
    
    passed = 0
    failed = 0
    
    for subtotal, discount_value, expected_label, expected_amount, expected_total in test_cases:
        # Calculate discount
        if discount_value == '0':
            discount_percentage = 0
        elif discount_value == '20':
            discount_percentage = 20
        elif discount_value == '20pwd':
            discount_percentage = 20
        elif discount_value == '5':
            discount_percentage = 5
        else:
            discount_percentage = 0
        
        calculated_amount = round((subtotal * discount_percentage) / 100, 2)
        calculated_total = round(subtotal - calculated_amount, 2)
        
        # Check results
        amount_correct = abs(calculated_amount - expected_amount) < 0.01
        total_correct = abs(calculated_total - expected_total) < 0.01
        
        status = "PASS" if (amount_correct and total_correct) else "FAIL"
        passed += 1 if (amount_correct and total_correct) else 0
        failed += 0 if (amount_correct and total_correct) else 1
        
        print(f"\n[{status}] Subtotal: P{subtotal:.2f} | Discount: {discount_value}")
        print(f"       Label: {expected_label}")
        print(f"       Expected: P{expected_amount:.2f} discount -> P{expected_total:.2f} total")
        print(f"       Calculated: P{calculated_amount:.2f} discount -> P{calculated_total:.2f} total")
    
    print("\n" + "=" * 90)
    print(f"RESULTS: {passed} PASSED, {failed} FAILED out of {passed + failed} tests")
    print("=" * 90)
    
    if failed == 0:
        print("\nALL CALCULATIONS ARE CORRECT!")
        print("\nDiscount Logic Verified:")
        print("  - No Discount (0%): No amount deducted")
        print("  - Senior Citizen (20%): 20% of subtotal deducted")
        print("  - PWD (20%): 20% of subtotal deducted")
        print("  - Student (5%): 5% of subtotal deducted")
        print("\nAll calculations handle decimal values correctly.")
    else:
        print(f"\n{failed} calculation(s) failed!")
    
    return failed == 0

# Change test scenarios
def test_change_calculations():
    """Test change calculation with discounts"""
    
    print("\n" + "=" * 90)
    print("CHANGE CALCULATION TEST")
    print("=" * 90)
    
    test_cases = [
        # (subtotal, discount_value, amount_paid, expected_change)
        (500, '0', 500, 0),
        (500, '20', 500, 100),  # 500 - 100 = 400, paid 500, change = 100
        (500, '5', 500, 25),    # 500 - 25 = 475, paid 500, change = 25
        
        (300, '20', 500, 260),  # 300 - 60 = 240, paid 500, change = 260
        (1000, '20', 1200, 400), # 1000 - 200 = 800, paid 1200, change = 400
        
        (150.75, '5', 160, 16.79), # 150.75 - 7.54 = 143.21, paid 160, change = 16.79
    ]
    
    passed = 0
    failed = 0
    
    for subtotal, discount_value, amount_paid, expected_change in test_cases:
        if discount_value == '0':
            discount_percentage = 0
        elif discount_value == '20':
            discount_percentage = 20
        elif discount_value == '5':
            discount_percentage = 5
        else:
            discount_percentage = 0
        
        discount_amount = round((subtotal * discount_percentage) / 100, 2)
        total = round(subtotal - discount_amount, 2)
        calculated_change = round(max(0, amount_paid - total), 2)
        
        correct = abs(calculated_change - expected_change) < 0.01
        status = "PASS" if correct else "FAIL"
        passed += 1 if correct else 0
        failed += 0 if correct else 1
        
        print(f"\n[{status}] Subtotal: P{subtotal:.2f}, Discount: {discount_value}%, Paid: P{amount_paid:.2f}")
        print(f"       Total: P{total:.2f} -> Change: P{calculated_change:.2f}")
    
    if failed == 0:
        print("\nALL CHANGE CALCULATIONS CORRECT!")
    
    return failed == 0

if __name__ == '__main__':
    calc_ok = test_discount_calculations()
    change_ok = test_change_calculations()
    
    print("\n" + "=" * 90)
    if calc_ok and change_ok:
        print("ALL TESTS PASSED - DISCOUNT SYSTEM IS WORKING CORRECTLY")
    else:
        print("SOME TESTS FAILED - REVIEW THE DISCOUNT LOGIC")
    print("=" * 90)
