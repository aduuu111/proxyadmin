# Architecture Documentation

ProxyAdminPanel 系统架构详细说明。

## 系统架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户浏览器                               │
│                     (http://localhost:3000)                      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP/HTTPS
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                        前端层 (Vue 3)                            │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Login   │  │Dashboard │  │  Users   │  │Outbounds │       │
│  │   Page   │  │   Page   │  │   List   │  │   List   │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │           Vue Router (路由管理)                     │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │           Pinia Store (状态管理)                    │        │
│  │  - Auth State (认证状态)                            │        │
│  │  - JWT Token Management                             │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │           Axios HTTP Client                         │        │
│  │  - 自动 Token 注入                                   │        │
│  │  - 统一错误处理                                      │        │
│  │  - 401 自动跳转                                      │        │
│  └────────────────────────────────────────────────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ REST API + JWT
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    BFF 层 (FastAPI Backend)                      │
│                     (http://localhost:8000)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │              FastAPI 路由层                          │        │
│  ├────────────────────────────────────────────────────┤        │
│  │  /api/auth/login          - 用户登录                │        │
│  │  /api/users/*             - 用户管理 CRUD            │        │
│  │  /api/outbounds/*         - 出站器管理 CRUD          │        │
│  │  /api/rules/*             - 规则管理 CRUD            │        │
│  │  /api/system/*            - 系统管理接口             │        │
│  └────────────────────────────────────────────────────┘        │
│                             │                                    │
│  ┌────────────────────────────────────────────────────┐        │
│  │              JWT 认证中间件                          │        │
│  │  - Token 验证                                        │        │
│  │  - 用户身份识别                                      │        │
│  │  - 权限检查                                          │        │
│  └────────────────────────────────────────────────────┘        │
│                             │                                    │
│  ┌────────────────────────────────────────────────────┐        │
│  │            业务逻辑层 (Services)                     │        │
│  ├────────────────────────────────────────────────────┤        │
│  │  UserService          - 用户管理逻辑                 │        │
│  │  │ - 创建/更新/删除用户                              │        │
│  │  │ - 状态同步 (DB ↔ Core)                          │        │
│  │  │ - 过期检测                                        │        │
│  │  │ - 流量管理                                        │        │
│  │                                                      │        │
│  │  OutboundService      - 出站器管理逻辑               │        │
│  │  │ - CRUD 操作                                      │        │
│  │  │ - 网卡扫描                                        │        │
│  │  │ - Core 同步                                      │        │
│  │                                                      │        │
│  │  RuleService          - 规则管理逻辑                 │        │
│  │  SystemService        - 系统管理逻辑                 │        │
│  └────────────────────────────────────────────────────┘        │
│                             │                                    │
│  ┌────────────────────────────────────────────────────┐        │
│  │         数据访问层 (SQLAlchemy ORM)                 │        │
│  ├────────────────────────────────────────────────────┤        │
│  │  Admin Model          - 管理员表                    │        │
│  │  User Model           - 用户表                      │        │
│  │  Outbound Model       - 出站器表                    │        │
│  │  Rule Model           - 规则表                      │        │
│  │  UserRule Model       - 用户-规则关联表             │        │
│  └────────────────────────────────────────────────────┘        │
│                             │                                    │
│  ┌────────────────────────────────────────────────────┐        │
│  │              SQLite 数据库                           │        │
│  │           (proxy_admin.db)                          │        │
│  │  - 持久化存储所有配置                                │        │
│  │  - 单一数据源                                        │        │
│  │  - 事务支持                                          │        │
│  └────────────────────────────────────────────────────┘        │
│                                                                  │
│  ┌────────────────────────────────────────────────────┐        │
│  │           Core Adapter (httpx Client)               │        │
│  │  - 封装 Core Service API                            │        │
│  │  - 异步 HTTP 请求                                    │        │
│  │  - 错误处理                                          │        │
│  │  - API Key 认证                                      │        │
│  └────────────────────────────────────────────────────┘        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP + API Key
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 核心服务层 (Core Service)                        │
│                   (配置的 Core API URL)                          │
├─────────────────────────────────────────────────────────────────┤
│  - 实际的代理服务执行                                             │
│  - 流量转发                                                      │
│  - 连接管理                                                      │
│  - 带宽限速                                                      │
│  - 规则匹配                                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 数据流向

### 1. 用户创建流程

```
前端表单提交
    │
    ├─> POST /api/users
    │
    ├─> FastAPI Router (users.py)
    │   └─> JWT 验证
    │
    ├─> UserService.create()
    │   ├─> 1. 验证数据 (端口冲突检查)
    │   ├─> 2. 创建 User 对象
    │   ├─> 3. 保存到 SQLite ✓
    │   ├─> 4. 判断状态
    │   │   ├─ enable=True && 未过期
    │   │   │  └─> CoreAdapter.create_user()
    │   │   │      └─> Core Service 创建代理用户
    │   │   │
    │   │   └─ enable=False || 已过期
    │   │      └─> 不推送到 Core (仅存数据库)
    │   │
    │   └─> 5. 返回 User 对象
    │
    └─> 返回 JSON 响应到前端
        └─> 前端刷新用户列表
```

### 2. 用户状态变更流程

```
用户过期检测:
    │
    ├─> SystemService.check_expired_users()
    │   ├─> 查询 expire_time <= now 的用户
    │   ├─> 更新数据库状态为 "expired"
    │   └─> CoreAdapter.delete_user()
    │       └─> Core Service 删除该用户
    │
    └─> 用户无法再使用代理服务

用户续期:
    │
    ├─> UserService.renew_user()
    │   ├─> 更新 expire_time 为未来时间
    │   ├─> 设置 enable=True
    │   ├─> 更新数据库状态为 "active"
    │   └─> CoreAdapter.sync_user()
    │       └─> Core Service 创建/更新用户
    │
    └─> 用户恢复使用代理服务
```

### 3. 一键扫描流程

```
前端点击 "Scan Local IPs"
    │
    ├─> POST /api/outbounds/scan
    │
    ├─> OutboundService.scan_local_interfaces()
    │   ├─> 1. CoreAdapter.get_interfaces()
    │   │   └─> Core Service 返回网卡列表
    │   │       [
    │   │         {ehName: "eth0", eh: "192.168.1.1", ip: "1.2.3.4"},
    │   │         {ehName: "eth1", eh: "10.0.0.1", ip: "5.6.7.8"}
    │   │       ]
    │   │
    │   ├─> 2. 遍历每个网卡
    │   │   ├─> 生成唯一名称: direct_eth0_192_168_1_1
    │   │   ├─> 检查是否已存在
    │   │   └─> 创建 Outbound 对象
    │   │       ├─> 保存到数据库
    │   │       └─> CoreAdapter.create_outbound()
    │   │           └─> Core Service 创建出站器
    │   │
    │   └─> 3. 返回创建的出站器列表
    │
    └─> 前端显示成功消息并刷新列表
```

## 认证流程

### JWT 认证架构

```
1. 登录流程:
   ┌──────────┐
   │  用户输入  │
   │ username  │
   │ password  │
   └─────┬────┘
         │
         ▼
   ┌─────────────┐
   │POST /login  │
   └─────┬───────┘
         │
         ▼
   ┌──────────────────┐
   │ 验证密码 (bcrypt) │
   └─────┬────────────┘
         │ ✓ 成功
         ▼
   ┌──────────────────┐
   │  生成 JWT Token   │
   │ (30 天有效期)     │
   └─────┬────────────┘
         │
         ▼
   ┌──────────────────┐
   │ 返回 access_token │
   └─────┬────────────┘
         │
         ▼
   ┌──────────────────┐
   │ 前端存储 Token    │
   │ localStorage      │
   └──────────────────┘

2. 请求认证流程:
   ┌──────────────────┐
   │  前端发送请求     │
   │ + Bearer Token   │
   └─────┬────────────┘
         │
         ▼
   ┌──────────────────┐
   │  Axios拦截器      │
   │ 注入 Token        │
   └─────┬────────────┘
         │
         ▼
   ┌──────────────────┐
   │ FastAPI中间件     │
   │ 验证 JWT          │
   └─────┬────────────┘
         │
         ├─ ✓ 有效 ──> 继续处理请求
         │
         └─ ✗ 无效 ──> 返回 401
                        │
                        ▼
                   前端跳转登录页
```

## 数据库 Schema

```sql
-- 管理员表
CREATE TABLE admins (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    avatar VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 出站器表
CREATE TABLE outbounds (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    protocol VARCHAR(20) NOT NULL DEFAULT 'direct',
    config JSON NOT NULL,
    local_interface_ip VARCHAR(50),
    remark TEXT,
    is_auto_generated BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 规则表
CREATE TABLE rules (
    id INTEGER PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    priority INTEGER DEFAULT 0,
    remark TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户表
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    port INTEGER UNIQUE NOT NULL,
    protocol VARCHAR(20) NOT NULL DEFAULT 'socks5',
    total_traffic BIGINT DEFAULT 0,
    up_traffic BIGINT DEFAULT 0,
    down_traffic BIGINT DEFAULT 0,
    expire_time DATETIME NOT NULL,
    last_seen DATETIME,
    enable BOOLEAN NOT NULL DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'active',
    send_limit INTEGER DEFAULT 0,
    receive_limit INTEGER DEFAULT 0,
    max_conn_count INTEGER DEFAULT 0,
    outbound_id INTEGER NOT NULL,
    config JSON,
    remark TEXT,
    email VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (outbound_id) REFERENCES outbounds(id)
);

-- 用户-规则关联表
CREATE TABLE user_rules (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    rule_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_id) REFERENCES rules(id) ON DELETE CASCADE
);
```

## 关系模型

```
┌─────────┐
│  Admin  │ (1 个默认管理员)
└─────────┘

┌──────────┐         ┌──────┐         ┌──────┐
│ Outbound │◄───N:1──┤ User ├──M:N───►│ Rule │
└──────────┘         └──────┘         └──────┘
                         │
                         │ 1:N
                         ▼
                    ┌──────────┐
                    │UserRule  │ (关联表)
                    └──────────┘

关系说明:
- 一个 User 必须关联一个 Outbound (N:1)
- 一个 User 可以关联多个 Rule (M:N)
- 一个 Outbound 可以被多个 User 使用 (1:N)
- 一个 Rule 可以被多个 User 使用 (1:N)
```

## API 设计原则

### RESTful 风格

```
资源           方法      路径                    说明
---------------------------------------------------------
用户          GET       /api/users             获取所有用户
              GET       /api/users/{id}        获取单个用户
              POST      /api/users             创建用户
              PUT       /api/users/{id}        更新用户
              DELETE    /api/users/{id}        删除用户

出站器        GET       /api/outbounds         获取所有出站器
              POST      /api/outbounds         创建出站器
              PUT       /api/outbounds/{id}    更新出站器
              DELETE    /api/outbounds/{id}    删除出站器

规则          GET       /api/rules             获取所有规则
              POST      /api/rules             创建规则
              ...

特殊操作      POST      /api/users/{id}/reset-traffic  (非标准RESTful)
              POST      /api/users/{id}/toggle
              POST      /api/outbounds/scan
```

### 响应格式

**成功响应** (200):
```json
{
  "id": 1,
  "username": "testuser",
  "port": 1080,
  ...
}
```

**错误响应** (4xx/5xx):
```json
{
  "detail": "Port 1080 is already in use"
}
```

**列表响应**:
```json
[
  {...},
  {...}
]
```

## 错误处理策略

### 分层错误处理

```
1. Core Service 层:
   CoreAdapter
   └─> 捕获所有 httpx 异常
       └─> 抛出 CoreConnectionError
           └─> 包含详细错误信息

2. Service 层:
   UserService, OutboundService 等
   └─> 捕获 CoreConnectionError
       └─> 记录日志 (print)
       └─> 继续执行 (不影响数据库操作)
       └─> 或抛出 ValueError (业务错误)

3. Router 层:
   FastAPI 路由
   └─> 捕获 ValueError
       └─> 返回 400 Bad Request
   └─> 其他异常
       └─> FastAPI 自动处理 → 500

4. 前端层:
   Axios 拦截器
   └─> 捕获所有错误响应
       └─> 显示友好错误消息 (ElMessage)
       └─> 401 → 跳转登录
```

## 性能优化

### 1. 数据库优化
- ✅ 异步 SQLAlchemy (async/await)
- ✅ 索引: username, port, name (唯一索引)
- ✅ 懒加载关系 (默认)
- ✅ 批量操作支持

### 2. API 优化
- ✅ 异步路由 (async def)
- ✅ 依赖注入 (Depends)
- ✅ 数据验证缓存 (Pydantic)
- ✅ CORS 中间件

### 3. 前端优化
- ✅ 路由懒加载 (动态 import)
- ✅ Element Plus 按需引入 (Tree-shaking)
- ✅ Vite 快速构建
- ✅ 生产环境代码压缩

## 安全措施

### 1. 认证安全
- ✅ JWT Token (HS256)
- ✅ bcrypt 密码哈希 (10 轮)
- ✅ Token 过期机制 (30天)
- ✅ 自动登出

### 2. API 安全
- ✅ 所有路由需要认证 (除登录)
- ✅ CORS 限制
- ✅ 请求超时 (10秒)
- ✅ SQL 注入防护 (ORM)

### 3. 数据安全
- ✅ 密码不可逆加密
- ✅ 敏感数据不记录日志
- ✅ 数据库文件权限控制
- ✅ 定期备份

## 扩展性设计

### 水平扩展
- 数据库: SQLite → PostgreSQL
- 缓存: 添加 Redis
- 会话: 分布式 Session
- 负载均衡: Nginx

### 垂直扩展
- 多进程: Gunicorn workers
- 连接池: SQLAlchemy pool
- 异步任务: Celery

### 功能扩展
- 插件系统
- Webhook 通知
- 多租户支持
- 审计日志

---

**架构版本**: 1.0.0
**最后更新**: 2025-11-26
