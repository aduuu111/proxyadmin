# 部署方案 / Deployment Options

## 方案 1：使用 Git 仓库（推荐）

### 步骤 1：推送代码到 Git 仓库

```bash
# 初始化 Git（如果还没有）
git init
git add .
git commit -m "Initial commit"

# 添加远程仓库
git remote add origin https://github.com/yourusername/proxyadmin.git

# 推送代码
git push -u origin main
```

### 步骤 2：修改安装脚本

编辑 `xui.sh`，修改以下配置：

```bash
REPO_URL="https://github.com/yourusername/proxyadmin.git"  # 你的仓库地址
USE_GIT=true  # 使用 Git 方式
```

### 步骤 3：上传安装脚本

```bash
# 上传到你的服务器
scp xui.sh user@47.129.171.69:/var/www/downloads/
```

### 步骤 4：用户安装

用户执行：
```bash
wget http://47.129.171.69/downloads/xui.sh && chmod 777 xui.sh && ./xui.sh
```

---

## 方案 2：使用压缩包

### 步骤 1：在 Linux/WSL 上打包

```bash
# 在 Linux 或 WSL 中执行
chmod +x package.sh
./package.sh
```

这会创建 `proxyadmin.tar.gz` 文件。

### 步骤 2：上传文件

```bash
# 上传压缩包和安装脚本
scp proxyadmin.tar.gz user@47.129.171.69:/var/www/downloads/
scp xui.sh user@47.129.171.69:/var/www/downloads/
```

### 步骤 3：修改安装脚本

编辑 `xui.sh`，修改配置：

```bash
DOWNLOAD_URL="http://47.129.171.69/downloads/proxyadmin.tar.gz"
USE_GIT=false  # 使用下载方式
```

### 步骤 4：用户安装

用户执行：
```bash
wget http://47.129.171.69/downloads/xui.sh && chmod 777 xui.sh && ./xui.sh
```

---

## 方案 3：直接在服务器上部署（测试用）

如果你有服务器访问权限，可以直接部署：

```bash
# 1. 上传项目文件
scp -r . user@your-server:/tmp/proxyadmin/

# 2. SSH 到服务器
ssh user@your-server

# 3. 运行安装脚本
cd /tmp/proxyadmin
chmod +x xui.sh
sudo ./xui.sh
```

---

## 推荐方案

**推荐使用方案 1（Git 仓库）**，因为：
- ✅ 更新方便（git pull）
- ✅ 版本控制
- ✅ 不需要手动打包
- ✅ 支持持续部署

---

## 配置核心服务

安装完成后，编辑配置文件：

```bash
sudo nano /etc/proxyadmin/core_config.ini
```

修改为你的核心服务信息：

```ini
[core_service]
api_url = http://your-core-service:port
api_key = your-api-key
timeout = 10
```

重启服务：

```bash
sudo systemctl restart proxyadmin
```

---

## 验证安装

```bash
# 检查服务状态
systemctl status proxyadmin

# 查看日志
journalctl -u proxyadmin -f

# 测试 API
curl http://localhost:8000/docs
```

访问面板：`http://your-server-ip`
