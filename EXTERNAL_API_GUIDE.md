# External API Integration Guide

## Overview

The ProxyAdminPanel now supports external system integration through API keys. This allows third-party systems (payment processors, customer portals, automation tools) to interact with the proxy management system programmatically.

## Authentication

### API Key Authentication

External systems use API keys instead of JWT tokens for authentication.

**Header Format:**
```
X-API-Key: pak_your_api_key_here
```

### Creating an API Key

Only administrators can create API keys through the admin panel.

**Endpoint:** `POST /api/api-keys/`

**Request:**
```json
{
  "name": "Payment System Integration",
  "can_read": true,
  "can_write": true,
  "can_delete": false,
  "rate_limit_per_minute": 60,
  "expires_at": "2025-12-31T23:59:59Z"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Payment System Integration",
  "api_key": "pak_abc123...",
  "key_prefix": "pak_abc123",
  "is_active": true,
  "can_read": true,
  "can_write": true,
  "can_delete": false,
  "rate_limit_per_minute": 60,
  "expires_at": "2025-12-31T23:59:59Z",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Important:** Save the `api_key` value securely - it won't be shown again!

## API Endpoints

### 1. User Provisioning

Provision a new user after payment or signup.

**Endpoint:** `POST /api/external/users/provision`

**Headers:**
```
X-API-Key: pak_your_api_key_here
Content-Type: application/json
```

**Request:**
```json
{
  "username": "user123",
  "password": "securepass",
  "port": 10001,
  "protocol": "socks5",
  "expire_days": 30,
  "total_traffic_gb": 100,
  "outbound_id": 1,
  "rule_ids": [1, 2],
  "email": "user@example.com",
  "remark": "Premium plan"
}
```

**Response:**
```json
{
  "id": 123,
  "username": "user123",
  "port": 10001,
  "protocol": "socks5",
  "expire_time": "2025-02-01T00:00:00Z",
  "total_traffic": 107374182400,
  "enable": true,
  "status": "active",
  ...
}
```

### 2. User Renewal

Renew a user's subscription (extend expiration and add traffic).

**Endpoint:** `POST /api/external/users/{user_id}/renew`

**Request:**
```json
{
  "user_id": 123,
  "extend_days": 30,
  "add_traffic_gb": 50
}
```

**Response:**
```json
{
  "id": 123,
  "username": "user123",
  "expire_time": "2025-03-01T00:00:00Z",
  "total_traffic": 161061273600,
  "enable": true,
  "status": "active",
  ...
}
```

### 3. Get User Information

Retrieve user details by ID or username.

**By ID:** `GET /api/external/users/{user_id}`

**By Username:** `GET /api/external/users/username/{username}`

**Response:**
```json
{
  "id": 123,
  "username": "user123",
  "port": 10001,
  "protocol": "socks5",
  "total_traffic": 107374182400,
  "up_traffic": 1073741824,
  "down_traffic": 2147483648,
  "expire_time": "2025-02-01T00:00:00Z",
  "enable": true,
  "status": "active",
  ...
}
```

### 4. Batch User Creation

Create multiple users in a single request.

**Endpoint:** `POST /api/external/users/batch`

**Request:**
```json
{
  "users": [
    {
      "username": "user1",
      "password": "pass1",
      "port": 10001,
      "protocol": "socks5",
      "expire_time": "2025-02-01T00:00:00Z",
      "outbound_id": 1
    },
    {
      "username": "user2",
      "password": "pass2",
      "port": 10002,
      "protocol": "socks5",
      "expire_time": "2025-02-01T00:00:00Z",
      "outbound_id": 1
    }
  ]
}
```

**Response:**
```json
{
  "success_count": 2,
  "failure_count": 0,
  "results": [
    {
      "success": true,
      "user_id": 123,
      "username": "user1",
      "port": 10001
    },
    {
      "success": true,
      "user_id": 124,
      "username": "user2",
      "port": 10002
    }
  ]
}
```

### 5. Batch User Update

Update multiple users in a single request.

**Endpoint:** `PUT /api/external/users/batch`

**Request:**
```json
{
  "updates": [
    {
      "user_id": 123,
      "updates": {
        "total_traffic": 214748364800,
        "expire_time": "2025-03-01T00:00:00Z"
      }
    },
    {
      "user_id": 124,
      "updates": {
        "enable": false
      }
    }
  ]
}
```

**Response:**
```json
{
  "success_count": 2,
  "failure_count": 0,
  "results": [
    {
      "success": true,
      "user_id": 123,
      "username": "user1"
    },
    {
      "success": true,
      "user_id": 124,
      "username": "user2"
    }
  ]
}
```

### 6. Webhooks

#### Payment Webhook

Receive payment notifications from external systems.

**Endpoint:** `POST /api/external/webhooks/payment`

**Request:**
```json
{
  "event": "payment.success",
  "data": {
    "user_id": 123,
    "amount": 10.00,
    "currency": "USD",
    "transaction_id": "txn_123456"
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

**Supported Events:**
- `payment.success` - Successful payment (create or renew user)
- `payment.refund` - Payment refunded (disable user)

#### User Event Webhook

Receive user event notifications.

**Endpoint:** `POST /api/external/webhooks/user-event`

**Request:**
```json
{
  "event": "user.created",
  "data": {
    "user_id": 123,
    "username": "user123"
  },
  "timestamp": "2025-01-01T00:00:00Z"
}
```

**Supported Events:**
- `user.created` - User was created
- `user.updated` - User was updated
- `user.deleted` - User was deleted

## API Key Management

### List All API Keys

**Endpoint:** `GET /api/api-keys/`

**Authentication:** JWT (Admin only)

### Get API Key Details

**Endpoint:** `GET /api/api-keys/{key_id}`

**Authentication:** JWT (Admin only)

### Toggle API Key Status

**Endpoint:** `POST /api/api-keys/{key_id}/toggle`

**Authentication:** JWT (Admin only)

### Delete API Key

**Endpoint:** `DELETE /api/api-keys/{key_id}`

**Authentication:** JWT (Admin only)

## Permissions

API keys have three permission levels:

- **Read:** Can query user information and system data
- **Write:** Can create and update users, provision accounts
- **Delete:** Can delete users and resources

## Rate Limiting

Each API key has a configurable rate limit (default: 60 requests/minute).

Exceeding the rate limit will result in HTTP 429 (Too Many Requests) responses.

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message here"
}
```

**Common Status Codes:**
- `401 Unauthorized` - Invalid or missing API key
- `403 Forbidden` - API key lacks required permission
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation error
- `429 Too Many Requests` - Rate limit exceeded

## Example Integration (Python)

```python
import requests

API_BASE_URL = "http://localhost:8000"
API_KEY = "pak_your_api_key_here"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Provision a new user
def provision_user(username, password, port, expire_days=30):
    response = requests.post(
        f"{API_BASE_URL}/api/external/users/provision",
        headers=headers,
        json={
            "username": username,
            "password": password,
            "port": port,
            "protocol": "socks5",
            "expire_days": expire_days,
            "total_traffic_gb": 100,
            "outbound_id": 1,
            "rule_ids": [1]
        }
    )
    return response.json()

# Renew a user
def renew_user(user_id, extend_days=30, add_traffic_gb=50):
    response = requests.post(
        f"{API_BASE_URL}/api/external/users/{user_id}/renew",
        headers=headers,
        json={
            "user_id": user_id,
            "extend_days": extend_days,
            "add_traffic_gb": add_traffic_gb
        }
    )
    return response.json()

# Get user info
def get_user(user_id):
    response = requests.get(
        f"{API_BASE_URL}/api/external/users/{user_id}",
        headers=headers
    )
    return response.json()

# Example usage
user = provision_user("testuser", "testpass", 10001)
print(f"Created user: {user['username']} (ID: {user['id']})")

renewed = renew_user(user['id'], extend_days=30)
print(f"Renewed user until: {renewed['expire_time']}")
```

## Example Integration (JavaScript/Node.js)

```javascript
const axios = require('axios');

const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'pak_your_api_key_here';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Provision a new user
async function provisionUser(username, password, port, expireDays = 30) {
  const response = await axios.post(
    `${API_BASE_URL}/api/external/users/provision`,
    {
      username,
      password,
      port,
      protocol: 'socks5',
      expire_days: expireDays,
      total_traffic_gb: 100,
      outbound_id: 1,
      rule_ids: [1]
    },
    { headers }
  );
  return response.data;
}

// Renew a user
async function renewUser(userId, extendDays = 30, addTrafficGb = 50) {
  const response = await axios.post(
    `${API_BASE_URL}/api/external/users/${userId}/renew`,
    {
      user_id: userId,
      extend_days: extendDays,
      add_traffic_gb: addTrafficGb
    },
    { headers }
  );
  return response.data;
}

// Get user info
async function getUser(userId) {
  const response = await axios.get(
    `${API_BASE_URL}/api/external/users/${userId}`,
    { headers }
  );
  return response.data;
}

// Example usage
(async () => {
  const user = await provisionUser('testuser', 'testpass', 10001);
  console.log(`Created user: ${user.username} (ID: ${user.id})`);

  const renewed = await renewUser(user.id, 30);
  console.log(`Renewed user until: ${renewed.expire_time}`);
})();
```

## Security Best Practices

1. **Store API keys securely** - Never commit API keys to version control
2. **Use HTTPS in production** - Always use encrypted connections
3. **Rotate keys regularly** - Create new keys and delete old ones periodically
4. **Limit permissions** - Only grant the minimum required permissions
5. **Monitor usage** - Check `last_used_at` timestamps for suspicious activity
6. **Set expiration dates** - Use `expires_at` for temporary integrations

## OpenAPI Documentation

Full OpenAPI 3.1.0 specification is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- JSON: `http://localhost:8000/openapi.json`
