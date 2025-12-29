# 部署方案 / Deployment Options

## 方案 1：使用 Git 仓库（推荐）✅

### 步骤 1：代码已推送到 GitHub

仓库地址：https://github.com/aduuu111/proxyadmin

### 步骤 2：一键安装

用户在 Debian/Ubuntu 系统上执行：

```bash
wget https://raw.githubusercontent.com/aduuu111/proxyadmin/main/xui.sh && chmod +x xui.sh && sudo ./xui.sh
```

安装脚本会自动：
- 从 GitHub 克隆代码
- 安装所有依赖（Python 3, Node.js, Nginx）
- 构建前端
- 配置 systemd 服务
- 设置 Nginx 反向代理

---

## 方案 2：使用压缩包（备选）

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
