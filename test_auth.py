"""Test API key authentication"""
import requests
import json
import random

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8"

# Use random port to avoid conflicts
random_port = random.randint(20000, 30000)
random_username = f"testuser{random_port}"

# Test provision user endpoint
headers = {
    "Content-Type": "application/json",
    "auth": API_KEY
}

data = {
    "username": random_username,
    "password": "Pass@123",
    "port": random_port,
    "protocol": "socks5",
    "expire_days": 30,
    "total_traffic_gb": 100,
    "outbound_id": 1,
    "rule_ids": [1],
    "email": f"{random_username}@example.com",
    "remark": "Test"
}

print(f"Testing with API key: {API_KEY[:20]}...")
print(f"Headers: {headers}")
print(f"URL: {BASE_URL}/api/external/users/provision")

response = requests.post(
    f"{BASE_URL}/api/external/users/provision",
    headers=headers,
    json=data
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response: {response.text}")
