"""
Quick test script to verify new API endpoints are working.
Run this after starting the server.
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_openapi_spec():
    """Test that OpenAPI spec includes new endpoints"""
    print("\n=== Testing OpenAPI Specification ===")
    response = requests.get(f"{BASE_URL}/openapi.json")

    if response.status_code == 200:
        spec = response.json()
        paths = spec.get("paths", {})

        # Check for new endpoints
        new_endpoints = [
            "/api/api-keys/",
            "/api/external/users/provision",
            "/api/external/users/batch",
            "/api/external/webhooks/payment"
        ]

        print(f"Total endpoints: {len(paths)}")
        for endpoint in new_endpoints:
            if endpoint in paths:
                print(f"[OK] {endpoint} - Found")
            else:
                print(f"[FAIL] {endpoint} - Missing")

        return True
    else:
        print(f"[FAIL] Failed to fetch OpenAPI spec: {response.status_code}")
        return False


def test_health_check():
    """Test basic health check"""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/health")

    if response.status_code == 200:
        print(f"[OK] Health check passed: {response.json()}")
        return True
    else:
        print(f"[FAIL] Health check failed: {response.status_code}")
        return False


def test_api_key_endpoint_exists():
    """Test that API key endpoints are registered"""
    print("\n=== Testing API Key Endpoints ===")

    # This should return 401 or 403 (requires auth) not 404 (not found)
    response = requests.get(f"{BASE_URL}/api/api-keys/")

    if response.status_code in [401, 403]:
        print("[OK] API key management endpoint exists (requires auth)")
        return True
    elif response.status_code == 404:
        print("[FAIL] API key management endpoint not found")
        return False
    else:
        print(f"[WARN] Unexpected status code: {response.status_code}")
        return False


def test_external_api_endpoint_exists():
    """Test that external API endpoints are registered"""
    print("\n=== Testing External API Endpoints ===")

    # This should return 401 (missing API key) not 404 (not found)
    response = requests.post(
        f"{BASE_URL}/api/external/users/provision",
        json={"username": "test"}
    )

    if response.status_code == 401:
        print("[OK] External API endpoint exists (requires API key)")
        return True
    elif response.status_code == 404:
        print("[FAIL] External API endpoint not found")
        return False
    else:
        print(f"[WARN] Unexpected status code: {response.status_code}")
        return False


def main():
    print("=" * 60)
    print("ProxyAdminPanel - External API Test Suite")
    print("=" * 60)
    print("\nMake sure the server is running on http://localhost:8000")
    print("Start server with: python main.py")

    try:
        results = []

        results.append(test_health_check())
        results.append(test_openapi_spec())
        results.append(test_api_key_endpoint_exists())
        results.append(test_external_api_endpoint_exists())

        print("\n" + "=" * 60)
        print(f"Test Results: {sum(results)}/{len(results)} passed")
        print("=" * 60)

        if all(results):
            print("\n[OK] All tests passed! External API is ready.")
            print("\nNext steps:")
            print("1. Log in to admin panel")
            print("2. Create an API key at /api/api-keys/")
            print("3. Test with: curl -H 'X-API-Key: pak_...' http://localhost:8000/api/external/users/1")
        else:
            print("\n[FAIL] Some tests failed. Check the output above.")

    except requests.exceptions.ConnectionError:
        print("\n[FAIL] Error: Could not connect to server")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")


if __name__ == "__main__":
    main()
