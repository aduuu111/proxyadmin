# Testing Guide - ProxyAdminPanel

快速测试指南,确保系统正常运行。

## 前置要求

在开始测试前,请确保:

1. ✅ Python 3.10+ 已安装
2. ✅ Node.js 16+ 已安装
3. ✅ Core Service 正在运行
4. ✅ 已配置 `.env` 文件

## 快速检查清单

### 环境检查

```bash
# 检查 Python 版本
python --version  # 应该 >= 3.10

# 检查 Node 版本
node --version    # 应该 >= 16

# 检查 Core Service 连通性
curl -H "Auth: your-api-key" http://127.0.0.1:8080/api/system/getInterFaces
```

## 后端测试

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

预期输出: 所有依赖成功安装,无错误

### 2. 初始化数据库

```bash
python init_db.py
```

预期输出:
```
Initializing database...
Database tables created successfully.
Default admin created successfully!
Username: admin
Password: admin
Please change the default password after first login.

Database initialization completed!
```

验证:
```bash
# 检查数据库文件是否创建
ls proxy_admin.db
```

### 3. 启动后端

```bash
python main.py
```

预期输出:
```
Starting ProxyAdminPanel...
Database initialized.
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 4. 测试后端端点

在新终端中运行:

```bash
# 测试健康检查
curl http://localhost:8000/health

# 预期输出: {"status":"healthy"}

# 测试根端点
curl http://localhost:8000/

# 预期输出: {"message":"ProxyAdminPanel API","version":"1.0.0","docs":"/docs"}

# 测试登录
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# 预期输出: {"access_token":"eyJ...(JWT token)","token_type":"bearer"}
```

### 5. 访问 API 文档

浏览器打开: http://localhost:8000/docs

预期看到: 完整的 Swagger UI 文档界面,包含所有 API 端点

## 前端测试

### 1. 安装依赖

```bash
cd frontend
npm install
```

预期输出: 所有依赖成功安装,无警告

### 2. 启动开发服务器

```bash
npm run dev
```

预期输出:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:3000/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

### 3. 访问前端

浏览器打开: http://localhost:3000

预期看到: 登录页面,带有 ProxyAdminPanel 标题

### 4. 测试登录流程

1. 输入默认凭据:
   - Username: `admin`
   - Password: `admin`

2. 点击 **Login** 按钮

预期结果:
- ✅ 显示 "Login successful" 消息
- ✅ 自动跳转到 Dashboard
- ✅ 侧边栏显示菜单项
- ✅ 顶部显示用户名 "admin"

### 5. 测试 Dashboard

在 Dashboard 页面检查:

- ✅ CPU Usage 卡片显示数据
- ✅ Memory Usage 卡片显示数据
- ✅ Total Users 显示 0
- ✅ Active Users 显示 0
- ✅ Bandwidth Statistics 卡片存在
- ✅ System Information 卡片显示版本信息
- ✅ Quick Actions 按钮可见

点击 **Backup Database** 按钮:
- ✅ 开始下载 .db 文件
- ✅ 显示成功消息

## 功能测试

### 测试出站器管理

1. 进入 **Outbounds** 页面

2. 点击 **Scan Local IPs** 按钮
   - ✅ 显示确认对话框
   - ✅ 确认后显示成功消息
   - ✅ 表格显示自动创建的出站器

3. 点击 **Add Outbound** 按钮
   - ✅ 弹出对话框
   - ✅ 填写表单:
     - Name: `test-outbound`
     - Protocol: `direct`
     - Local Interface IP: `192.168.1.1`
     - Remark: `Test outbound`
   - ✅ 点击 Confirm
   - ✅ 显示成功消息
   - ✅ 新出站器出现在列表中

4. 测试编辑和删除
   - ✅ 点击 Edit 按钮,表单预填充数据
   - ✅ 点击 Delete 按钮,显示确认对话框
   - ✅ 确认后出站器被删除

### 测试规则管理

1. 进入 **Rules** 页面

2. 点击 **Add Rule** 按钮
   - ✅ 填写表单:
     - Name: `allow-all`
     - Content: `* = allow`
     - Priority: `100`
     - Remark: `Allow all traffic`
   - ✅ 点击 Confirm
   - ✅ 规则创建成功

3. 查看规则示例卡片
   - ✅ 显示规则格式说明
   - ✅ 包含多个示例

### 测试用户管理

1. 进入 **Users** 页面

2. 确保至少有一个出站器和规则

3. 点击 **Add User** 按钮
   - ✅ 填写表单:
     - Remark: `Test User`
     - Port: `1080`
     - Username: `testuser`
     - Password: `testpass`
     - Protocol: `socks5`
     - Outbound: 选择一个出站器
     - Rules: 选择至少一个规则
     - Traffic Limit: `10` (GB)
     - Expiration Date: 选择未来日期
     - Enable: 勾选
   - ✅ 点击 Confirm
   - ✅ 用户创建成功
   - ✅ 状态显示为 "Active" (绿色)

4. 测试用户操作:
   - ✅ 点击 **Reset** - 确认流量重置
   - ✅ 点击 **Disable** - 状态变为 "Disabled" (灰色)
   - ✅ 点击 **Enable** - 状态恢复 "Active"
   - ✅ 点击 **Edit** - 修改用户信息
   - ✅ 点击 **Delete** - 删除用户

5. 测试过期用户:
   - 创建一个过期日期为过去的用户
   - ✅ 状态自动显示为 "Expired" (红色)
   - ✅ 编辑用户,将过期时间改为未来
   - ✅ 启用后状态变为 "Active"

### 测试设置页面

1. 进入 **Settings** 页面

2. 测试密码修改:
   - Username: `admin`
   - New Password: `newpassword123`
   - Confirm Password: `newpassword123`
   - ✅ 点击 Save Changes
   - ✅ 显示成功消息

3. 测试登出和新密码登录:
   - ✅ 点击顶部 Logout 按钮
   - ✅ 返回登录页
   - ✅ 使用新密码登录成功

## Core Service 集成测试

### 测试 Core 同步

1. **准备工作**:
   - 确保 Core Service 正在运行
   - 在 Core Service 中清空所有用户和出站器

2. **创建出站器**:
   - 在面板中创建出站器
   - 使用 Core Service API 验证:
     ```bash
     curl -H "Auth: your-api-key" http://127.0.0.1:8080/api/out/getOutBoundsAll
     ```
   - ✅ 应该能看到新创建的出站器

3. **创建用户**:
   - 在面板中创建启用的用户
   - 使用 Core Service API 验证:
     ```bash
     curl -H "Auth: your-api-key" http://127.0.0.1:8080/api/user/getUserAll
     ```
   - ✅ 应该能看到新创建的用户

4. **测试用户禁用**:
   - 在面板中禁用用户
   - 再次查询 Core Service
   - ✅ 用户应该被删除

5. **测试用户续期**:
   - 创建一个已过期的用户
   - ✅ 验证 Core Service 中没有该用户
   - 在面板中编辑,设置未来过期时间并启用
   - ✅ 验证 Core Service 中出现该用户

## 性能测试

### 并发测试

使用 Apache Bench 测试:

```bash
# 测试登录端点
ab -n 100 -c 10 -p login.json -T application/json http://localhost:8000/api/auth/login

# login.json 内容:
# {"username":"admin","password":"admin"}
```

预期:
- ✅ 所有请求成功 (200 OK)
- ✅ 平均响应时间 < 100ms
- ✅ 无错误

### 负载测试

创建多个用户 (10-50 个):
- ✅ 面板响应流畅
- ✅ 数据库查询正常
- ✅ Core Service 同步成功

## 错误处理测试

### 测试网络错误

1. 停止 Core Service
2. 尝试创建用户
   - ✅ 显示友好错误消息
   - ✅ 数据仍保存到数据库
   - ✅ 前端不崩溃

3. 重启 Core Service
4. 编辑刚才创建的用户
   - ✅ 成功同步到 Core

### 测试验证错误

1. 尝试创建重复端口的用户
   - ✅ 显示 "Port xxx is already in use"

2. 尝试创建同名出站器
   - ✅ 显示 "Outbound with name 'xxx' already exists"

3. 尝试创建同名规则
   - ✅ 显示 "Rule with name 'xxx' already exists"

### 测试认证错误

1. 使用错误密码登录
   - ✅ 显示 "Incorrect username or password"

2. 访问 API 不带 Token
   - ✅ 返回 401 Unauthorized

3. 使用过期 Token
   - ✅ 自动跳转到登录页

## 浏览器兼容性测试

测试以下浏览器:

- ✅ Chrome (最新版本)
- ✅ Firefox (最新版本)
- ✅ Edge (最新版本)
- ✅ Safari (Mac 用户)

所有功能应正常工作,无布局问题。

## 移动端响应式测试

在浏览器开发者工具中测试:

1. 切换到移动设备视图
2. 测试各个页面
   - ✅ 布局适应屏幕
   - ✅ 按钮可点击
   - ✅ 表格可滚动

## 数据持久性测试

1. 创建一些用户、出站器、规则
2. 停止后端服务
3. 重启后端服务
4. ✅ 所有数据依然存在
5. ✅ 状态正确

## 备份恢复测试

1. 创建测试数据
2. 点击 Dashboard 的 **Backup Database**
3. 下载 .db 文件
4. 停止服务
5. 删除原数据库: `rm proxy_admin.db`
6. 恢复备份: `cp backup_file.db proxy_admin.db`
7. 重启服务
8. ✅ 所有数据恢复正常

## 常见问题排查

### 后端无法启动

```bash
# 检查端口占用
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 检查数据库
python -c "import sqlite3; print(sqlite3.connect('proxy_admin.db').execute('SELECT COUNT(*) FROM admins').fetchone())"
```

### 前端连接失败

```bash
# 检查后端是否运行
curl http://localhost:8000/health

# 检查 Vite 代理配置
cat frontend/vite.config.js
```

### Core Service 连接失败

```bash
# 测试 Core Service 连通性
curl -H "Auth: your-api-key" http://127.0.0.1:8080/api/system/getInterFaces

# 检查 .env 配置
cat .env | grep CORE_
```

## 测试完成清单

完成以下所有项目表示系统测试通过:

- [ ] 后端成功启动
- [ ] 数据库初始化成功
- [ ] API 文档可访问
- [ ] 前端成功启动
- [ ] 登录功能正常
- [ ] Dashboard 显示正常
- [ ] 出站器 CRUD 正常
- [ ] 规则 CRUD 正常
- [ ] 用户 CRUD 正常
- [ ] 一键扫描功能正常
- [ ] 流量重置功能正常
- [ ] 用户启用/禁用正常
- [ ] 数据库备份正常
- [ ] 设置修改正常
- [ ] Core Service 同步正常
- [ ] 错误处理友好
- [ ] 性能可接受

## 下一步

测试通过后:

1. ✅ 修改默认密码
2. ✅ 配置生产环境 `.env`
3. ✅ 阅读 `DEPLOYMENT.md` 进行生产部署
4. ✅ 设置定时备份任务
5. ✅ 配置监控告警

---

**Happy Testing! 🎉**
