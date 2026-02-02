# DISCOUNT FEATURE - QUICK USER GUIDE

## 🎯 How to Use the Enhanced Discount Feature

### Option 1: Use a Quick Preset
The fastest way to apply a discount:

```
Step 1: Click one of the preset buttons
   [Senior (20%)]  [PWD (20%)]  [Student (5%)]

Step 2: (Optional) Edit the reason
   Reason: "Senior Citizen" → Change to "Senior with ID"

Step 3: Enter amount paid and process
```

**Result:** Discount automatically set with reason included in receipt

---

### Option 2: Custom Percent Discount
Apply a custom percentage discount (0-100%):

```
Step 1: Ensure "% Percent" is selected
   [% Percent] ← should be highlighted in red

Step 2: Enter discount percentage
   Input field: "15" (for 15% off)

Step 3: (Optional) Enter reason
   Reason: "Employee Discount"

Step 4: View summary and confirm
   Applied Discount: 15%
   Discount Amount: ₱XXX.XX
   Reason: Employee Discount

Step 5: Process payment
```

---

### Option 3: Fixed Peso Discount
Apply a fixed peso amount discount:

```
Step 1: Toggle to "₱ Pesos"
   [₱ Pesos] ← click to switch

Step 2: Enter peso amount
   Input field: "250" (for ₱250 off)
   
   ⚠️ Note: Cannot exceed the subtotal
   ⚠️ If you enter too much, error appears:
      "₱ Discount cannot exceed subtotal (₱1,500.00)"

Step 3: (Optional) Enter reason
   Reason: "Loyalty Discount"

Step 4: View summary and confirm
   Applied Discount: ₱250.00
   Discount Amount: ₱250.00
   Reason: Loyalty Discount

Step 5: Process payment
```

---

## 📋 Field Guide

### Discount Type Toggle
```
[% Percent] [₱ Pesos]
```
- **Red button** = Currently active
- **White button** = Inactive, click to switch
- Changes the symbol (% vs ₱) and input limits

### Quick Presets
```
[Senior (20%)] [PWD (20%)] [Student (5%)]
```
- Click any button to instantly fill in:
  - Discount type (Percent)
  - Discount value (20%, 20%, or 5%)
  - Reason field (Senior Citizen, PWD, Student)

### Discount Value Input
```
[%/₱]  [___Enter Amount___]  [Max: 100% / Subtotal]
```
- **Left symbol:** Changes based on selected type
- **Input field:** Type your discount value
- **Right hint:** Shows limit for current type
- Numbers only, can use decimals (e.g., 7.5, 125.50)

### Reason / Notes Field
```
[___Reason (optional)___]
Examples: Employee discount, Loyalty, Promotion
```
- Optional field
- Helps track WHY discount was given
- Appears on printed receipt
- Useful for audits

### Discount Summary (Auto-Display)
```
Applied Discount: 20% Off
Discount Amount: ₱300.00
Reason: Senior Citizen
```
- Appears when discount is valid
- Hidden if no discount selected
- Updates in real-time
- Hides if validation error occurs

---

## ✅ Validation Rules

### For Percent Discounts
| Entry | Status | Behavior |
|-------|--------|----------|
| 0 | Valid | No discount |
| 5 | Valid | 5% off |
| 50 | Valid | 50% off |
| 100 | Valid | 100% off (free!) |
| 150 | Invalid | ❌ Error: "Cannot exceed 100%" |
| -10 | Invalid | ❌ Converts to 0 |

### For Peso Discounts
| Entry | Status | Behavior |
|-------|--------|----------|
| ₱0 | Valid | No discount |
| ₱100 | Valid | If subtotal ≥ ₱100 |
| ₱500 | Valid | If subtotal ≥ ₱500 |
| ₱1000 | Invalid* | ❌ If subtotal = ₱800 |
| -50 | Invalid | ❌ Converts to 0 |

*Must not exceed subtotal amount

---

## 🔴 Error Messages

### "Discount cannot exceed 100%"
- **Cause:** Entered more than 100 for percent
- **Fix:** Change value to 100 or less
- **Auto-Fix:** On blur, automatically corrects to 100

### "₱ Discount cannot exceed subtotal (₱X,XXX.XX)"
- **Cause:** Peso amount is more than cart subtotal
- **Example:** ₱500 discount but subtotal only ₱300
- **Fix:** Enter a smaller peso amount
- **Prevention:** This discount won't be applied

---

## 💡 Tips & Tricks

### Tip 1: Reset to No Discount
- Clear the Discount Value field (leave it empty or 0)
- Summary will hide automatically
- Apply payment with no discount

### Tip 2: Switching Types
- Switch between Percent and Peso anytime
- Current value clears when switching
- Reason field stays (if you want to keep it)

### Tip 3: Combining with Presets
- Click a preset first (e.g., Senior 20%)
- Then manually change the percentage (e.g., to 15%)
- Reason stays as "Senior Citizen"
- Great for modified preset discounts!

### Tip 4: Quick Entry
- For presets: Just click the button → Done!
- For custom: Percent takes ~3 seconds
- For custom: Peso takes ~3 seconds
- Reason is optional, skip if not needed

### Tip 5: Verify Before Processing
- Always check the "Discount Summary" box
- Verify discount type (% or ₱)
- Verify discount amount
- Verify reason (if applicable)
- Then proceed with payment

---

## 📲 Receipt Shows

### With Senior Preset
```
Subtotal:                    ₱1,500.00
Discount (20% Off - Senior Citizen): -₱300.00
----------------------------------------
TOTAL:                       ₱1,200.00
Amount Paid:                 ₱1,200.00
Change:                            ₱0.00
```

### With Custom Peso Discount
```
Subtotal:                    ₱2,000.00
Discount (₱250.00 Off - Loyalty):  -₱250.00
----------------------------------------
TOTAL:                       ₱1,750.00
Amount Paid:                 ₱1,800.00
Change:                           ₱50.00
```

### With No Discount
```
Subtotal:                    ₱1,000.00
(No discount section)
----------------------------------------
TOTAL:                       ₱1,000.00
Amount Paid:                 ₱1,000.00
Change:                            ₱0.00
```

---

## ❓ FAQ

**Q: Can I use both percent AND peso discount at once?**
A: No, only one type per transaction. Choose either % or ₱.

**Q: What if I make a mistake?**
A: Edit the field or clear it. No payment is processed until you click "PRINT RECEIPT".

**Q: Is the reason field mandatory?**
A: No, it's optional. But it helps with tracking, so recommended!

**Q: Can I undo a discount after printing?**
A: No, the receipt is already printed. Be careful before processing.

**Q: What's the maximum discount I can give?**
A: Percent: 100% (free item)
  Peso: Up to the subtotal (free transaction)

**Q: Do discounts carry over to the next customer?**
A: No, they reset after each transaction. Start fresh every time!

---

## 🎓 Common Scenarios

### Scenario 1: Senior Customer
```
Customer: "I'm a senior citizen, can I get a discount?"

Action:
1. Click [Senior (20%)] button
2. See: 20% Off - Senior Citizen
3. Enter amount paid
4. Click PRINT RECEIPT

Result: Automatic 20% discount applied + tracked
```

### Scenario 2: Loyalty Customer (Percent)
```
Customer: "I'm a loyal customer, usually 10% off"

Action:
1. Make sure [% Percent] is selected
2. Enter value: 10
3. Enter reason: "Loyalty"
4. See summary update
5. Enter amount paid
6. Click PRINT RECEIPT

Result: 10% loyalty discount applied + tracked
```

### Scenario 3: Fixed Amount Gift
```
Manager: "Give this customer ₱150 discount"

Action:
1. Click [₱ Pesos] button
2. Enter value: 150
3. Enter reason: "Manager Approval" or "Promotion"
4. See summary update
5. Enter amount paid
6. Click PRINT RECEIPT

Result: ₱150 fixed discount applied + tracked
```

### Scenario 4: Wrong Discount Entry
```
You: "Oops, I entered 25% instead of 15%"

Action:
1. See error or summary with 25%
2. Click in Discount Value field
3. Clear it and enter: 15
4. Summary updates instantly
5. Everything is correct now!

Result: No harm done, discount corrected before payment
```

---

## 🛠️ Troubleshooting

| Problem | Solution |
|---------|----------|
| Button not responding | Click once and wait, don't double-click |
| Number won't enter | Make sure field is focused (click it first) |
| Error won't go away | Clear the field and re-enter a valid value |
| Summary not showing | Enter a valid discount value (0-100% or 0-Subtotal ₱) |
| Receipt missing reason | Make sure you typed in Reason field before processing |
| Amount keeps resetting | Don't click elsewhere while editing, use Tab or Enter |

---

**Version:** 2.0 (Enhanced)
**Last Updated:** February 2, 2026
**For Support:** Ask manager or IT support
