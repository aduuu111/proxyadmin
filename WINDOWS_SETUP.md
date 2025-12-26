# Windows 本地测试环境搭建指南

完整的 Windows 环境配置，用于本地测试后再部署到 Linux 服务器。

## 📋 前置要求检查

### 必须安装的软件

1. **Python 3.10 或更高版本**
   - 下载地址：https://www.python.org/downloads/
   - ⚠️ 安装时勾选 "Add Python to PATH"

2. **Node.js 16 或更高版本**
   - 下载地址：https://nodejs.org/
   - 推荐使用 LTS 版本（目前是 20.x）

3. **Git** (可选，用于版本控制)
   - 下载地址：https://git-scm.com/downloads

### 检查是否已安装

打开 **命令提示符** (CMD) 或 **PowerShell**，运行以下命令：

```bash
# 检查 Python 版本
python --version
# 应显示: Python 3.10.x 或更高

# 检查 pip 版本
pip --version

# 检查 Node.js 版本
node --version
# 应显示: v16.x.x 或更高

# 检查 npm 版本
npm --version
```

如果任何命令报错，说明对应软件未安装或未添加到 PATH。

---

## 🚀 快速开始（推荐）

### 方法一：使用自动启动脚本

1. **配置环境变量**
   ```bash
   # 在项目目录下
   cd E:\Akaifa\proxysell5

   # .env 文件已经创建，编辑配置
   notepad .env
   ```

   **必须修改的配置**：
   ```env
   # 你的 Core Service 地址
   CORE_API_URL=http://127.0.0.1:8080

   # 你的 Core Service API 密钥
   CORE_API_KEY=your_actual_api_key_here
   ```

2. **双击运行启动脚本**
   ```
   双击: E:\Akaifa\proxysell5\start.bat
   ```

   脚本会自动：
   - ✅ 检查 .env 文件
   - ✅ 初始化数据库
   - ✅ 启动后端服务

3. **启动前端（新开命令行窗口）**
   ```bash
   cd E:\Akaifa\proxysell5\frontend
   npm install
   npm run dev
   ```

4. **访问系统**
   - 前端：http://localhost:3000
   - 后端 API：http://localhost:8000/docs

---

## 🔧 方法二：手动安装（完整控制）

### 第一步：安装 Python 依赖

```bash
cd E:\Akaifa\proxysell5

# 升级 pip（推荐）
python -m pip install --upgrade pip

# 安装项目依赖
pip install -r requirements.txt
```

**依赖列表说明**：
- `fastapi` - Web 框架
- `uvicorn` - ASGI 服务器
- `sqlalchemy` - ORM 数据库工具
- `aiosqlite` - 异步 SQLite 驱动
- `python-jose` - JWT 认证
- `passlib` - 密码加密
- `httpx` - 异步 HTTP 客户端
- `pydantic` - 数据验证
- `python-dotenv` - 环境变量管理

**可能遇到的问题**：

**问题1：pip 下载速度慢**
```bash
# 使用清华大学镜像源
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**问题2：安装 cryptography 失败**
```bash
# 需要安装 Visual C++ 构建工具
# 下载地址：https://visualstudio.microsoft.com/visual-cpp-build-tools/
# 或者安装预编译的 wheel 包
pip install cryptography --only-binary :all:
```

### 第二步：初始化数据库

```bash
python init_db.py
```

**预期输出**：
```
Initializing database...
Database tables created successfully.
Default admin created successfully!
Username: admin
Password: admin
Please change the default password after first login.

Database initialization completed!
```

**验证**：
```bash
# 检查数据库文件是否创建
dir proxy_admin.db
```

### 第三步：启动后端服务

```bash
python main.py
```

**预期输出**：
```
Starting ProxyAdminPanel...
Database initialized.
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**后端运行地址**：
- API 服务：http://localhost:8000
- API 文档：http://localhost:8000/docs （Swagger UI）
- 健康检查：http://localhost:8000/health

### 第四步：安装前端依赖

**打开新的命令行窗口**：

```bash
cd E:\Akaifa\proxysell5\frontend

# 安装依赖（首次运行，需要几分钟）
npm install
```

**可能遇到的问题**：

**问题1：npm 安装速度慢**
```bash
# 使用淘宝镜像源
npm config set registry https://registry.npmmirror.com

# 重新安装
npm install
```

**问题2：权限错误**
```bash
# 清除缓存
npm cache clean --force

# 重新安装
npm install
```

### 第五步：启动前端服务

```bash
npm run dev
```

**预期输出**：
```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
➜  press h to show help
```

**前端运行地址**：http://localhost:3000

---

## 🧪 功能测试

### 1. 测试后端 API

打开浏览器或使用 `curl`：

```bash
# 健康检查
curl http://localhost:8000/health
# 应返回: {"status":"healthy"}

# 测试根路径
curl http://localhost:8000/
# 应返回: {"message":"ProxyAdminPanel API","version":"1.0.0","docs":"/docs"}

# 查看 API 文档
浏览器打开: http://localhost:8000/docs
```

### 2. 测试前端界面

1. 浏览器打开：http://localhost:3000
2. 应该看到登录页面
3. 使用默认账号登录：
   - 用户名：`admin`
   - 密码：`admin`
4. 成功登录后应跳转到 Dashboard

### 3. 测试核心功能

按照以下顺序测试：

#### Step 1: 扫描本机 IP
1. 进入 **Outbounds** 页面
2. 点击 **"Scan Local IPs"** 按钮
3. 确认扫描
4. 检查是否自动创建了 direct 出站器

#### Step 2: 创建规则
1. 进入 **Rules** 页面
2. 点击 **"Add Rule"** 按钮
3. 填写：
   - Name: `allow-all`
   - Content: `* = allow`
   - Priority: `100`
4. 保存

#### Step 3: 创建用户
1. 进入 **Users** 页面
2. 点击 **"Add User"** 按钮
3. 填写表单（选择已创建的出站器和规则）
4. 保存
5. 检查用户状态是否为 "Active"

#### Step 4: 测试其他功能
- ✅ 修改管理员密码（Settings 页面）
- ✅ 重置用户流量
- ✅ 启用/禁用用户
- ✅ 下载数据库备份
- ✅ 同步流量统计

---

## 🐛 常见问题排查

### 问题1：端口被占用

**后端 8000 端口被占用**：
```bash
# 查看占用进程
netstat -ano | findstr :8000

# 结束进程
taskkill /F /PID <进程号>
```

**前端 3000 端口被占用**：
- Vite 会自动使用下一个可用端口（3001, 3002...）

### 问题2：找不到 Python 模块

```bash
# 确认在正确的目录
cd E:\Akaifa\proxysell5

# 重新安装依赖
pip install -r requirements.txt

# 验证安装
pip list | findstr fastapi
```

### 问题3：数据库文件损坏

```bash
# 删除数据库
del proxy_admin.db

# 重新初始化
python init_db.py
```

### 问题4：前端页面空白

1. 打开浏览器开发者工具（F12）
2. 查看 Console 标签是否有错误
3. 查看 Network 标签，检查 API 请求是否成功
4. 确认后端服务正在运行

### 问题5：Core Service 连接失败

```bash
# 测试 Core Service 连通性
curl -H "Auth: your-api-key" http://127.0.0.1:8080/api/system/getInterFaces

# 检查 .env 配置
type .env | findstr CORE_
```

如果连接失败：
- ✅ 确认 Core Service 正在运行
- ✅ 检查 `CORE_API_URL` 是否正确
- ✅ 检查 `CORE_API_KEY` 是否正确
- ✅ 检查防火墙是否阻止连接

---

## 📊 性能测试（可选）

### 测试工具推荐

**ApacheBench (ab)**：
- 下载地址：https://www.apachehaus.com/cgi-bin/download.plx
- 解压后将 bin 目录添加到 PATH

**测试登录接口**：
```bash
# 创建测试数据文件 login.json
echo {"username":"admin","password":"admin"} > login.json

# 发送 100 个请求，10 个并发
ab -n 100 -c 10 -p login.json -T application/json http://localhost:8000/api/auth/login
```

**预期结果**：
- 所有请求成功 (200 OK)
- 平均响应时间 < 100ms

---

## 🎯 测试完成清单

在部署到服务器前，请确保以下功能都已测试：

- [ ] 后端服务启动成功
- [ ] 前端界面可访问
- [ ] 登录功能正常
- [ ] Dashboard 显示数据
- [ ] 扫描本机 IP 功能正常
- [ ] 创建出站器成功
- [ ] 创建规则成功
- [ ] 创建用户成功
- [ ] 用户状态同步到 Core Service
- [ ] 流量重置功能正常
- [ ] 启用/禁用用户正常
- [ ] 数据库备份功能正常
- [ ] 修改管理员密码成功
- [ ] 测试用户过期自动禁用

**全部测试通过后，即可准备部署到 Linux 服务器！**

---

## 📝 准备部署

测试通过后，准备以下信息：

1. **服务器信息**
   - 系统版本（Debian/Ubuntu 版本号）
   - IP 地址和 SSH 端口
   - SSH 登录凭据

2. **域名（可选但推荐）**
   - 用于配置 HTTPS
   - DNS 解析到服务器 IP

3. **Core Service 信息**
   - Core Service 部署地址
   - API Key

4. **备份当前配置**
   ```bash
   # 备份 .env 文件
   copy .env .env.backup

   # 备份数据库（如果有测试数据）
   copy proxy_admin.db proxy_admin.db.backup
   ```

---

## 🚀 下一步：Linux 部署

Windows 测试通过后，查看：
- **Ubuntu/Debian 部署指南**：LINUX_DEPLOYMENT.md
- **完整部署文档**：DEPLOYMENT.md

---

## 💡 提示

- 在 Windows 测试时，使用 **相对路径** 和 **环境变量**，方便迁移到 Linux
- 不要在 Windows 测试环境中使用生产数据
- 定期备份测试数据库
- 记录遇到的问题和解决方案

---

有任何问题随时询问！
