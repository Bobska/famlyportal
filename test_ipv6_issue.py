"""Test IPv6 vs IPv4 connectivity to Google APIs"""
import socket
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

print("\n" + "="*60)
print("Testing IPv4 vs IPv6 Connectivity")
print("="*60)

# Test IPv4
print("\n1. Testing IPv4 connection to gmail.googleapis.com...")
try:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Force IPv4
    sock.settimeout(10)
    sock.connect(('gmail.googleapis.com', 443))
    print("   ✅ IPv4 connection successful!")
    sock.close()
except Exception as e:
    print(f"   ❌ IPv4 connection failed: {e}")

# Test IPv6
print("\n2. Testing IPv6 connection to gmail.googleapis.com...")
try:
    sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)  # Force IPv6
    sock.settimeout(10)
    sock.connect(('gmail.googleapis.com', 443))
    print("   ✅ IPv6 connection successful!")
    sock.close()
except Exception as e:
    print(f"   ❌ IPv6 connection failed: {e}")

# Test default (what Python uses)
print("\n3. Testing default socket connection (what Python chooses)...")
try:
    sock = socket.create_connection(('gmail.googleapis.com', 443), timeout=10)
    print(f"   ✅ Default connection successful!")
    print(f"   Family: {sock.family.name}")
    sock.close()
except Exception as e:
    print(f"   ❌ Default connection failed: {e}")

print("\n" + "="*60)
print("DIAGNOSIS:")
print("="*60)
print("If IPv4 works but IPv6 fails, we need to force IPv4 in Python.")
print("="*60 + "\n")
