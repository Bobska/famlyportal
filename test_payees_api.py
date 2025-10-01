#!/usr/bin/env python
"""
Test script to check payees API endpoint and verify category data is included
"""
import requests
import json

# Start a session
session = requests.Session()

# Try to access the payees endpoint
try:
    response = session.get('http://127.0.0.1:8000/budget-basic/payees/')
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print("Response data:")
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print("Response content (not JSON):")
            print(response.text[:500])
    else:
        print("Response content:")
        print(response.text[:500])
        
except Exception as e:
    print(f"Error: {e}")