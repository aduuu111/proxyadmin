# API响应格式说明

## 版本: 2.1.0

## 成功响应格式

### 1. 创建用户 (POST /api/external/users/provision)
**状态码**: 201 Created
**响应格式**: 返回完整的用户对象
```json
{
  "id": 1,
  "username": "user001",
  "port": 10001,
  "protocol": "socks5",
  "total_traffic": 107374182400,
  "up_traffic": 0,
  "down_traffic": 0,
  "expire_time": "2026-01-22T08:00:00",
  "enable": true,
  "status": "active",
  "email": "user@example.com",
  "remark": "Basic Plan",
  "created_at": "2025-12-23T08:00:00",
  "updated_at": "2025-12-23T08:00:00"
}
```

### 2. 查询用户 (GET /api/external/users/port/{port})
**状态码**: 200 OK
**响应格式**: 返回完整的用户对象
```json
{
  "id": 1,
  "username": "user001",
  "port": 10001,
  ...
}
```

### 3. 续费用户 (POST /api/external/users/port/{port}/renew)
**状态码**: 200 OK
**响应格式**: 返回更新后的用户对象
```json
{
  "id": 1,
  "username": "user001",
  "port": 10001,
  "total_traffic": 161061273600,
  "expire_time": "2026-02-22T08:00:00",
  ...
}
```

### 4. 启用/禁用用户 (POST /api/external/users/port/{port}/toggle)
**状态码**: 200 OK
**响应格式**: 返回更新后的用户对象
```json
{
  "id": 1,
  "username": "user001",
  "port": 10001,
  "enable": false,
  ...
}
```

### 5. 删除用户 (DELETE /api/external/users/port/{port})
**状态码**: 200 OK
**响应格式**: 返回成功消息
```json
{
  "message": "User on port 10001 deleted successfully"
}
```

### 6. 批量创建用户 (POST /api/external/users/batch)
**状态码**: 200 OK
**响应格式**: 返回批量操作结果
```json
{
  "success_count": 2,
  "failure_count": 1,
  "results": [
    {
      "success": true,
      "user_id": 1,
      "username": "user001",
      "port": 10001
    },
    {
      "success": true,
      "user_id": 2,
      "username": "user002",
      "port": 10002
    },
    {
      "success": false,
      "username": "user003",
      "error": "Port 10003 is already in use"
    }
  ]
}
```

### 7. 批量删除用户 (DELETE /api/external/users/batch)
**状态码**: 200 OK
**响应格式**: 返回批量操作结果
```json
{
  "success_count": 2,
  "failure_count": 1,
  "results": [
    {
      "success": true,
      "port": 10001,
      "username": "user001"
    },
    {
      "success": true,
      "port": 10002,
      "username": "user002"
    },
    {
      "success": false,
      "port": 10003,
      "error": "User with port 10003 not found"
    }
  ]
}
```

## 错误响应格式

### 1. 未授权 (401 Unauthorized)
**原因**: API密钥无效或缺失
```json
{
  "detail": "Invalid or inactive API key"
}
```

### 2. 权限不足 (403 Forbidden)
**原因**: API密钥缺少所需权限
```json
{
  "detail": "API key does not have delete permission"
}
```

### 3. 资源未找到 (404 Not Found)
**原因**: 请求的资源不存在
```json
{
  "detail": "User with port 10001 not found"
}
```

### 4. 服务器错误 (500 Internal Server Error)
**原因**: 服务器内部错误
```json
{
  "detail": "Internal server error"
}
```

## 响应格式规范

### 成功响应
- **数据操作** (GET, POST renew/toggle, POST provision): 返回完整的数据对象
- **删除操作** (DELETE): 返回成功消息对象 `{"message": "..."}`
- **批量操作**: 返回批量操作结果对象，包含成功/失败统计和详细结果列表

### 错误响应
- 所有错误响应都包含 `detail` 字段，提供清晰的错误描述
- 使用标准HTTP状态码表示错误类型
- 错误消息使用英文，便于程序处理

## 状态码总结

| 状态码 | 说明 | 使用场景 |
|--------|------|----------|
| 200 | 成功 | 查询、更新、删除操作成功 |
| 201 | 已创建 | 资源创建成功 |
| 401 | 未授权 | API密钥无效或缺失 |
| 403 | 禁止访问 | API密钥权限不足 |
| 404 | 未找到 | 请求的资源不存在 |
| 500 | 服务器错误 | 服务器内部错误 |
