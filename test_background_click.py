#!/usr/bin/env python3
"""
Test script to validate the background click functionality in budget_basic app.
This script checks if the JavaScript code has the correct event listeners setup.
"""

import os
import re

def test_background_click_functionality():
    """Test if the JavaScript has proper background click handling."""
    
    js_file_path = "budget_basic/static/budget_basic/js/budget_basic.js"
    
    if not os.path.exists(js_file_path):
        print("❌ JavaScript file not found:", js_file_path)
        return False
    
    with open(js_file_path, 'r', encoding='utf-8') as f:
        js_content = f.read()
    
    # Check for the initializeTransactionSelection function
    if 'function initializeTransactionSelection()' not in js_content:
        print("❌ initializeTransactionSelection function not found")
        return False
    else:
        print("✅ initializeTransactionSelection function found")
    
    # Check for transaction-cards-container event listener
    if "transactionCardsContainer.addEventListener('click'" not in js_content:
        print("❌ transactionCardsContainer click event listener not found")
        return False
    else:
        print("✅ transactionCardsContainer click event listener found")
    
    # Check for transaction-list-content event listener
    if "transactionListContainer.addEventListener('click'" not in js_content:
        print("❌ transactionListContainer click event listener not found")
        return False
    else:
        print("✅ transactionListContainer click event listener found")
    
    # Check for closest('.transaction-card-data') logic
    if "e.target.closest('.transaction-card-data')" not in js_content:
        print("❌ transaction-card-data detection logic not found")
        return False
    else:
        print("✅ transaction-card-data detection logic found")
    
    # Check for clearTransactionSelection calls
    clear_calls = js_content.count('clearTransactionSelection()')
    if clear_calls < 2:
        print(f"❌ Expected at least 2 clearTransactionSelection() calls, found {clear_calls}")
        return False
    else:
        print(f"✅ Found {clear_calls} clearTransactionSelection() calls")
    
    # Check for debug logging
    debug_logs = js_content.count('console.log')
    if debug_logs < 5:
        print(f"❌ Expected debug logging, found {debug_logs} console.log statements")
        return False
    else:
        print(f"✅ Found {debug_logs} debug console.log statements")
    
    # Check that the function is called in DOMContentLoaded
    if 'initializeTransactionSelection();' not in js_content:
        print("❌ initializeTransactionSelection() not called in DOMContentLoaded")
        return False
    else:
        print("✅ initializeTransactionSelection() is called in DOMContentLoaded")
    
    print("\n🎉 All JavaScript background click functionality tests passed!")
    return True

def check_html_structure():
    """Check if the HTML has the correct structure for background clicking."""
    
    html_file_path = "budget_basic/templates/budget_basic/main.html"
    
    if not os.path.exists(html_file_path):
        print("❌ HTML template file not found:", html_file_path)
        return False
    
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Check for required containers
    required_elements = [
        'transaction-cards-container',
        'transaction-list-content',
        'transaction-card-data',
        'onclick="selectTransaction(this)"'
    ]
    
    for element in required_elements:
        if element not in html_content:
            print(f"❌ Required HTML element/attribute not found: {element}")
            return False
        else:
            print(f"✅ Found HTML element/attribute: {element}")
    
    print("\n🎉 All HTML structure tests passed!")
    return True

if __name__ == "__main__":
    print("Testing Background Click Functionality\n")
    print("=" * 50)
    
    js_test_passed = test_background_click_functionality()
    print("\n" + "=" * 50)
    html_test_passed = check_html_structure()
    
    print("\n" + "=" * 50)
    if js_test_passed and html_test_passed:
        print("🎉 ALL TESTS PASSED! Background click functionality should work.")
        print("\nTo manually test:")
        print("1. Run: python manage.py runserver")
        print("2. Login at: http://127.0.0.1:8000/accounts/login/ (admin/admin123)")
        print("3. Go to: http://127.0.0.1:8000/budget-basic/transactions/")
        print("4. Click on a transaction to select it")
        print("5. Click anywhere in the left panel header or empty space")
        print("6. The transaction should be deselected and right panel should clear")
        print("7. Check browser console for debug messages")
    else:
        print("❌ TESTS FAILED! Check the issues above.")