# 安全的API密钥使用指南

## ✅ 已完成的安全改进

### 1. 移除公开的API密钥创建端点
- **原因**: 防止任何人通过接口创建API密钥
- **改进**: API密钥管理端点已从系统中移除
- **创建方式**: 只能通过服务器端脚本创建

### 2. 预生成的API密钥
**API密钥**: `pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8`

**权限**:
- 读权限: ✓
- 写权限: ✓
- 删除权限: ✗
- 速率限制: 60 请求/分钟
- 有效期: 2026-12-21

### 3. 简化的认证头部
- **头部名称**: `auth` (不再是 `X-API-Key`)
- **使用方式**: `auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8`

## 📦 Apifox导入步骤

### 1. 导入OpenAPI文件
1. 打开Apifox
2. 点击 **"导入"** → **"导入数据"**
3. 选择 **"OpenAPI/Swagger"**
4. 选择文件: `apifox-test-collection.json`
5. 点击 **"确认导入"**

### 2. 配置环境变量（可选）
API密钥已内置在OpenAPI文件中，Apifox会自动识别。

如需手动配置:
- 变量名: `apiKey`
- 值: `pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8`

### 3. 开始测试
所有接口已预配置好认证头部，直接点击"发送"即可测试！

## 🔧 如何创建新的API密钥

### 方法1: 使用脚本（推荐）
```bash
python create_api_key.py
```

脚本会:
1. 生成安全的API密钥
2. 保存到数据库
3. 显示完整密钥（只显示一次）

### 方法2: 自定义创建
修改 `create_api_key.py` 中的参数:
```python
api_key, db_key = await create_api_key(
    name="Custom API Key",
    can_read=True,
    can_write=True,
    can_delete=False,
    rate_limit_per_minute=120,  # 自定义速率限制
    expires_days=365  # 自定义有效期
)
```

## 📝 API端点列表

### 用户管理
- `POST /api/external/users/provision` - 开通用户
- `POST /api/external/users/{user_id}/renew` - 续费用户
- `GET /api/external/users/{user_id}` - 查询用户（按ID）
- `GET /api/external/users/username/{username}` - 查询用户（按用户名）

### 批量操作
- `POST /api/external/users/batch` - 批量创建用户
- `PUT /api/external/users/batch` - 批量更新用户

### Webhook
- `POST /api/external/webhooks/payment` - 支付回调
- `POST /api/external/webhooks/user-event` - 用户事件回调

### 系统
- `GET /health` - 健康检查

## 🧪 测试示例

### 1. 开通用户
```bash
curl --location --request POST 'http://localhost:8000/api/external/users/provision' \
--header 'auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8' \
--header 'Content-Type: application/json' \
--data-raw '{
    "username": "test001",
    "password": "Pass@123",
    "port": 10001,
    "protocol": "socks5",
    "expire_days": 30,
    "total_traffic_gb": 100,
    "outbound_id": 1,
    "rule_ids": [1],
    "email": "test001@example.com",
    "remark": "测试用户"
}'
```

### 2. 查询用户
```bash
curl --location --request GET 'http://localhost:8000/api/external/users/1' \
--header 'auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8'
```

### 3. 续费用户
```bash
curl --location --request POST 'http://localhost:8000/api/external/users/1/renew' \
--header 'auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8' \
--header 'Content-Type: application/json' \
--data-raw '{
    "user_id": 1,
    "extend_days": 30,
    "add_traffic_gb": 50
}'
```

### 4. 批量创建
```bash
curl --location --request POST 'http://localhost:8000/api/external/users/batch' \
--header 'auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8' \
--header 'Content-Type: application/json' \
--data-raw '{
    "users": [
        {
            "username": "batch001",
            "password": "Pass001",
            "port": 11001,
            "protocol": "socks5",
            "expire_time": "2025-02-15T00:00:00Z",
            "total_traffic": 107374182400,
            "outbound_id": 1
        }
    ]
}'
```

## 🔒 安全最佳实践

1. **保护API密钥**: 不要将密钥提交到版本控制系统
2. **定期轮换**: 定期创建新密钥并删除旧密钥
3. **最小权限**: 根据需要分配权限（读/写/删除）
4. **监控使用**: 检查 `last_used_at` 字段监控异常活动
5. **设置过期**: 为临时集成设置过期时间

## 📊 文件说明

- `create_api_key.py` - API密钥生成脚本
- `apifox-test-collection.json` - Apifox测试集合（OpenAPI格式）
- `EXTERNAL_API_GUIDE.md` - 完整API集成指南
- `IMPLEMENTATION_SUMMARY.md` - 技术实现总结

## ⚠️ 重要提示

1. **API密钥管理端点已移除**: 无法通过HTTP接口创建密钥
2. **只能通过脚本创建**: 使用 `create_api_key.py` 创建新密钥
3. **密钥只显示一次**: 创建时立即保存，无法再次查看
4. **服务器已自动重启**: 修改会自动生效

## 🎯 快速开始

1. 确保服务器运行: `python main.py`
2. 导入 `apifox-test-collection.json` 到Apifox
3. 使用预设密钥开始测试
4. 所有接口已配置好认证，直接发送请求即可！

---

**预设API密钥**: `pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8`

**认证���部**: `auth: pak_RmrxXpqSzEGA0etV7fbS-_lqnNbqq3dV2RygoxkiIn8`
