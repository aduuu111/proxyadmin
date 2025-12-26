"""Test all API endpoints to verify response formats"""
import requests
import random

BASE_URL = "http://127.0.0.1:8000"
API_KEY = "pak_uPGliB1Jnvt7gt8PGdwBgaqj4Ahyqu-NSkMeUN9EDWk"
headers = {"Content-Type": "application/json", "auth": API_KEY}

print("=" * 60)
print("API Response Format Test")
print("=" * 60)

# Test port
test_port = random.randint(20000, 21000)

# 1. Test provision (create user)
print(f"\n1. POST /api/external/users/provision (port {test_port})")
response = requests.post(
    f"{BASE_URL}/api/external/users/provision",
    headers=headers,
    json={
        "username": f"testuser{test_port}",
        "password": "Pass@123",
        "port": test_port,
        "protocol": "socks5",
        "expire_days": 30,
        "total_traffic_gb": 50,
        "outbound_id": 1,
        "rule_ids": [1],
        "email": "test@example.com",
        "remark": "Response Test"
    }
)
print(f"   Status: {response.status_code}")
if response.status_code == 201:
    data = response.json()
    print(f"   [OK] User created: {data['username']}, port: {data['port']}")
else:
    print(f"   [FAIL] {response.text}")

# 2. Test get user by port
print(f"\n2. GET /api/external/users/port/{test_port}")
response = requests.get(f"{BASE_URL}/api/external/users/port/{test_port}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] User found: {data['username']}")
else:
    print(f"   [FAIL] {response.text}")

# 3. Test renew
print(f"\n3. POST /api/external/users/port/{test_port}/renew")
response = requests.post(
    f"{BASE_URL}/api/external/users/port/{test_port}/renew",
    headers=headers,
    json={"extend_days": 30, "add_traffic_gb": 50}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] User renewed: {data['username']}, traffic: {data['total_traffic'] / (1024**3):.0f}GB")
else:
    print(f"   [FAIL] {response.text}")

# 4. Test toggle
print(f"\n4. POST /api/external/users/port/{test_port}/toggle")
response = requests.post(f"{BASE_URL}/api/external/users/port/{test_port}/toggle", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] User toggled: enabled={data['enable']}")
else:
    print(f"   [FAIL] {response.text}")

# 5. Test delete
print(f"\n5. DELETE /api/external/users/port/{test_port}")
response = requests.delete(f"{BASE_URL}/api/external/users/port/{test_port}", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] {data['message']}")
else:
    print(f"   [FAIL] {response.text}")

# 6. Test batch delete
print(f"\n6. DELETE /api/external/users/batch")
test_ports = [random.randint(21000, 22000) for _ in range(3)]
# Create test users first
for port in test_ports:
    requests.post(
        f"{BASE_URL}/api/external/users/provision",
        headers=headers,
        json={
            "username": f"batchtest{port}",
            "password": "Pass@123",
            "port": port,
            "protocol": "socks5",
            "expire_days": 30,
            "total_traffic_gb": 50,
            "outbound_id": 1,
            "rule_ids": [1]
        }
    )

response = requests.delete(
    f"{BASE_URL}/api/external/users/batch",
    headers=headers,
    json={"ports": test_ports}
)
print(f"   Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] Batch delete: {data['success_count']} succeeded, {data['failure_count']} failed")
else:
    print(f"   [FAIL] {response.text}")

# 7. Test error cases
print(f"\n7. GET /api/external/users/port/99999 (non-existent)")
response = requests.get(f"{BASE_URL}/api/external/users/port/99999", headers=headers)
print(f"   Status: {response.status_code}")
if response.status_code == 404:
    data = response.json()
    print(f"   [OK] Error message: {data['detail']}")
else:
    print(f"   [FAIL] Expected 404")

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
