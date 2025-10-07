# Smart Filtering - Testing Guide

## Quick Testing Steps

### 1. Test Payee Filtering by Transaction Type
1. Open the Weekly view in Budget Basic
2. Click "Add Transaction" button
3. **Default State (Expense):**
   - Verify transaction type is set to "Expense"
   - Check payee dropdown only shows expense merchants
   - Check category dropdown only shows expense categories
   
4. **Switch to Income:**
   - Click "Income" radio button
   - Verify labels change (Amount Received, Received From, etc.)
   - **Check payee dropdown updates to show only income merchants**
   - **Check category dropdown updates to show only income categories**
   - Verify selections are cleared when switching types

5. **Switch back to Expense:**
   - Click "Expense" radio button
   - Verify dropdowns revert to expense payees/categories
   - Verify selections are cleared

### 2. Test Auto-Population When Adding Payee
1. Open Add Transaction modal
2. Select "Expense" transaction type
3. Click "+" button next to payee dropdown
4. **Verify:** Add Payee modal opens with "Expense" pre-selected in Type dropdown
5. Close modal

6. Switch to "Income" transaction type
7. Click "+" button next to payee dropdown
8. **Verify:** Add Payee modal opens with "Income" pre-selected in Type dropdown
9. Close modal

### 3. Test Auto-Population When Adding Category
1. Open Add Transaction modal
2. Select "Expense" transaction type
3. Click "+" button next to category dropdown
4. **Verify:** Add Category modal opens with "Expense" pre-selected in Type dropdown
5. Close modal

6. Switch to "Income" transaction type
7. Click "+" button next to category dropdown
8. **Verify:** Add Category modal opens with "Income" pre-selected in Type dropdown

### 4. Test End-to-End Workflow
**Scenario: Add a new income merchant and create transaction**

1. Open Add Transaction modal
2. Select "Income" transaction type
3. Click "+" next to payee dropdown
4. Add new merchant:
   - Name: "Freelance Client ABC"
   - Type: Should be pre-selected as "Income" ✓
   - Select a category or create one
   - Save
5. Verify new merchant appears in payee dropdown
6. Verify dropdown still only shows income merchants
7. Select the new merchant
8. Complete and save transaction
9. Verify transaction appears in weekly view

**Scenario: Prevent wrong type selection**

1. Create/identify an expense merchant (e.g., "Grocery Store")
2. Create/identify an income merchant (e.g., "Salary")
3. Open Add Transaction modal
4. Select "Income" type
5. **Verify:** "Grocery Store" should NOT appear in dropdown
6. **Verify:** "Salary" SHOULD appear in dropdown
7. Switch to "Expense" type
8. **Verify:** "Salary" should NOT appear in dropdown
9. **Verify:** "Grocery Store" SHOULD appear in dropdown

### 5. Edge Cases to Test

**No merchants of selected type:**
1. If no income merchants exist:
   - Select "Income" type
   - Verify dropdown shows only placeholder "Select existing payee..."
   - Add a new income merchant
   - Verify it appears immediately

**Rapid type switching:**
1. Rapidly click between Income and Expense types
2. Verify dropdowns update correctly each time
3. Verify no JavaScript errors in console
4. Verify selections are cleared properly

**Modal stacking:**
1. Add Transaction modal → Add Payee modal
2. Verify Add Payee modal appears on top
3. Verify transaction modal is faded in background
4. Save/close Add Payee modal
5. Verify transaction modal returns to normal

## Expected Results

✅ Payee dropdown filters by transaction_type matching selected type
✅ Category dropdown filters by transaction_type (already working)
✅ Add Payee modal pre-selects type based on transaction type
✅ Add Category modal pre-selects type based on transaction type
✅ Selections clear when switching types
✅ New merchants appear in correct filtered dropdown
✅ Cannot select wrong type merchant for transaction
✅ No JavaScript errors in console
✅ Smooth user experience with no lag

## Console Debugging

If issues occur, check browser console for:
```javascript
// Should see these logs:
"Opening Add Payee modal for: expense" or "income"
"Transaction type changed to: expense" or "income"

// Check payeeCache structure:
console.log(payeeCache);
// Each payee should have: {id, name, transaction_type, categories: [...]}

// Check filtering:
console.log(payeeCache.filter(p => p.transaction_type === 'expense'));
console.log(payeeCache.filter(p => p.transaction_type === 'income'));
```

## Database Verification

Check that payees have transaction_type set:
```sql
-- From Django shell or SQLite
SELECT id, name, transaction_type FROM budget_basic_payee;
```

Should see:
- Expense merchants with transaction_type = 'expense'
- Income merchants with transaction_type = 'income'

## Known Good State

After testing, you should have:
- ✅ At least one income merchant
- ✅ At least one expense merchant
- ✅ Income categories
- ✅ Expense categories
- ✅ Test transactions of both types
- ✅ All dropdowns filtering correctly
- ✅ Type pre-selection working in modals

## Rollback Plan

If issues occur:
```bash
# Revert commit
git revert 0c6ff88

# Or restore previous version
git checkout e096122 budget_basic/static/budget_basic/js/budget_basic.js
python manage.py collectstatic --no-input
```

## Success Criteria

Consider testing successful when:
1. All dropdowns filter correctly by type
2. Type pre-selection works in add modals
3. User cannot accidentally select wrong type merchants
4. No JavaScript errors occur
5. Workflow feels natural and prevents errors
6. New merchants appear in correct filtered dropdown immediately

---
**Test Date:** _____________
**Tested By:** _____________
**Result:** ☐ PASS  ☐ FAIL  ☐ NEEDS WORK
**Notes:** _____________________
