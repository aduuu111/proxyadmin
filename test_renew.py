"""Test user renewal by port"""
import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8"

# Use random port to avoid conflicts
test_port = random.randint(16000, 17000)

headers = {
    "Content-Type": "application/json",
    "auth": API_KEY
}

# Test 1: Create a user
print("=== Test 1: Create User ===")
create_data = {
    "username": f"renewtest{test_port}",
    "password": "Pass@123",
    "port": test_port,
    "protocol": "socks5",
    "expire_days": 30,
    "total_traffic_gb": 50,
    "outbound_id": 1,
    "rule_ids": [1],
    "email": "renewtest@example.com",
    "remark": "Renewal Test"
}

response = requests.post(
    f"{BASE_URL}/api/external/users/provision",
    headers=headers,
    json=create_data
)

print(f"Status: {response.status_code}")
if response.status_code == 201:
    user = response.json()
    print(f"Created user: {user['username']}, port: {user['port']}")
    print(f"Initial traffic: {user['total_traffic'] / (1024**3):.0f} GB")
    print(f"Expires: {user['expire_time']}")
else:
    print(f"Error: {response.text}")
    exit(1)

# Test 2: Renew user by port
print("\n=== Test 2: Renew User by Port ===")
renew_data = {
    "extend_days": 60,
    "add_traffic_gb": 100
}

response = requests.post(
    f"{BASE_URL}/api/external/users/port/{test_port}/renew",
    headers=headers,
    json=renew_data
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"Renewed user: {user['username']}, port: {user['port']}")
    print(f"New traffic: {user['total_traffic'] / (1024**3):.0f} GB")
    print(f"New expiration: {user['expire_time']}")
else:
    print(f"Error: {response.text}")

# Test 3: Get user by port
print("\n=== Test 3: Get User by Port ===")
response = requests.get(
    f"{BASE_URL}/api/external/users/port/{test_port}",
    headers=headers
)

print(f"Status: {response.status_code}")
if response.status_code == 200:
    user = response.json()
    print(f"User: {user['username']}, port: {user['port']}")
    print(f"Traffic: {user['total_traffic'] / (1024**3):.0f} GB")
    print(f"Status: {user['status']}, Enabled: {user['enable']}")
else:
    print(f"Error: {response.text}")

print("\n=== All Tests Completed ===")
