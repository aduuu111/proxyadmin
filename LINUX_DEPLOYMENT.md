# Linux (Debian/Ubuntu) 生产环境部署指南

完整的 Debian 和 Ubuntu 服务器部署文档，包含所有依赖安装和配置步骤。

## 📋 支持的系统版本

✅ **Debian**
- Debian 12 (Bookworm) - 推荐
- Debian 11 (Bullseye)
- Debian 10 (Buster)

✅ **Ubuntu**
- Ubuntu 24.04 LTS (Noble) - 推荐
- Ubuntu 22.04 LTS (Jammy) - 推荐
- Ubuntu 20.04 LTS (Focal)

## 🎯 部署架构选择

### 方案 A：Docker 部署（推荐，最简单）
- ✅ 环境隔离
- ✅ 一键部署
- ✅ 易于升级
- ✅ 适合新手

### 方案 B：Systemd + Nginx（生产级）
- ✅ 原生性能
- ✅ 完全控制
- ✅ 易于监控
- ✅ 适合进阶用户

我们将详细介绍两种方案。

---

## 🚀 方案 A：Docker 一键部署

### 前置要求

- 服务器运行 Debian/Ubuntu
- 至少 1GB 内存，2GB 推荐
- 至少 10GB 磁盘空间
- Root 或 sudo 权限

### 第一步：安装 Docker

```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装依赖
sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release

# 添加 Docker 官方 GPG key
curl -fsSL https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]')/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# 添加 Docker 仓库
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/$(lsb_release -is | tr '[:upper:]' '[:lower:]') $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# 安装 Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# 验证安装
sudo docker --version
sudo docker compose version

# 将当前用户加入 docker 组（可选）
sudo usermod -aG docker $USER
# 注销并重新登录以生效
```

### 第二步：准备项目文件

```bash
# 创建项目目录
sudo mkdir -p /opt/proxyadminpanel
cd /opt/proxyadminpanel

# 上传项目文件（方法1：使用 scp 从本地上传）
# 在你的 Windows 机器上运行：
# scp -r E:\Akaifa\proxysell5\* user@your-server-ip:/opt/proxyadminpanel/

# 或者方法2：使用 git
# git clone your-repository-url .

# 设置权限
sudo chown -R $USER:$USER /opt/proxyadminpanel
```

### 第三步：创建 Dockerfile

```bash
# 创建后端 Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "main.py"]
EOF
```

### 第四步：创建 docker-compose.yml

```bash
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: .
    container_name: proxyadmin-backend
    ports:
      - "8000:8000"
    volumes:
      - ./proxy_admin.db:/app/proxy_admin.db
      - ./.env:/app/.env
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
    networks:
      - proxyadmin-network

  frontend:
    image: node:20-alpine
    container_name: proxyadmin-frontend
    working_dir: /app
    command: sh -c "npm install && npm run build && npx serve -s dist -l 3000"
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
    restart: unless-stopped
    networks:
      - proxyadmin-network

networks:
  proxyadmin-network:
    driver: bridge
EOF
```

### 第五步：配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（使用 nano 或 vi）
nano .env
```

**重要配置项**：
```env
# Core Service 配置（必须修改）
CORE_API_URL=http://your-core-service:port
CORE_API_KEY=your_actual_api_key

# 生产环境 SECRET_KEY（必须修改）
SECRET_KEY=<使用下面命令生成>

# 管理员密码（建议修改）
DEFAULT_ADMIN_PASSWORD=your_strong_password
```

**生成安全的 SECRET_KEY**：
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
# 将输出的字符串复制到 .env 的 SECRET_KEY
```

### 第六步：初始化数据库

```bash
# 初始化数据库
docker compose run --rm backend python init_db.py
```

### 第七步：启动服务

```bash
# 构建并启动
sudo docker compose up -d

# 查看日志
sudo docker compose logs -f

# 检查服务状态
sudo docker compose ps
```

### 第八步：验证部署

```bash
# 检查后端健康
curl http://localhost:8000/health
# 应返回: {"status":"healthy"}

# 检查前端
curl http://localhost:3000
```

**访问系统**：
- 前端：http://your-server-ip:3000
- 后端 API：http://your-server-ip:8000/docs

---

## 🔧 方案 B：Systemd + Nginx 部署

### 第一步：安装系统依赖

```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装 Node.js 20
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# 安装 Nginx
sudo apt install -y nginx

# 安装其他工具
sudo apt install -y git curl wget build-essential

# 验证安装
python3.11 --version
node --version
nginx -v
```

### 第二步：准备应用

```bash
# 创建应用目录
sudo mkdir -p /opt/proxyadminpanel
cd /opt/proxyadminpanel

# 上传项目文件或使用 git clone
# scp -r E:\Akaifa\proxysell5\* user@your-server-ip:/opt/proxyadminpanel/

# 创建专用用户
sudo useradd -r -s /bin/bash -d /opt/proxyadminpanel proxyadmin
sudo chown -R proxyadmin:proxyadmin /opt/proxyadminpanel
```

### 第三步：配置 Python 虚拟环境

```bash
# 切换到应用目录
cd /opt/proxyadminpanel

# 创建虚拟环境
sudo -u proxyadmin python3.11 -m venv venv

# 激活虚拟环境并安装依赖
sudo -u proxyadmin bash -c "source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
```

### 第四步：配置环境变量

```bash
# 复制并编辑 .env
sudo -u proxyadmin cp .env.example .env
sudo -u proxyadmin nano .env
```

修改关键配置（同上）。

### 第五步：初始化数据库

```bash
sudo -u proxyadmin bash -c "source venv/bin/activate && python init_db.py"
```

### 第六步：构建前端

```bash
cd /opt/proxyadminpanel/frontend

# 安装依赖
sudo -u proxyadmin npm install

# 构建生产版本
sudo -u proxyadmin npm run build

# 构建后的文件在 dist/ 目录
ls -la dist/
```

### 第七步：配置 Systemd 服务

```bash
# 创建 systemd 服务文件
sudo nano /etc/systemd/system/proxyadmin.service
```

**服务文件内容**：
```ini
[Unit]
Description=ProxyAdminPanel Backend Service
After=network.target

[Service]
Type=simple
User=proxyadmin
Group=proxyadmin
WorkingDirectory=/opt/proxyadminpanel
Environment="PATH=/opt/proxyadminpanel/venv/bin"
ExecStart=/opt/proxyadminpanel/venv/bin/python main.py
Restart=always
RestartSec=10

# 日志
StandardOutput=journal
StandardError=journal
SyslogIdentifier=proxyadmin

[Install]
WantedBy=multi-user.target
```

**启动服务**：
```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start proxyadmin

# 设置开机自启
sudo systemctl enable proxyadmin

# 查看状态
sudo systemctl status proxyadmin

# 查看日志
sudo journalctl -u proxyadmin -f
```

### 第八步：配置 Nginx

```bash
# 创建 Nginx 配置文件
sudo nano /etc/nginx/sites-available/proxyadmin
```

**Nginx 配置内容**：
```nginx
server {
    listen 80;
    server_name your-domain.com;  # 改为你的域名或 IP

    # 前端静态文件
    location / {
        root /opt/proxyadminpanel/frontend/dist;
        try_files $uri $uri/ /index.html;

        # 缓存静态资源
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Gzip 压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

**启用站点并重启 Nginx**：
```bash
# 创建软链接
sudo ln -s /etc/nginx/sites-available/proxyadmin /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启 Nginx
sudo systemctl restart nginx

# 设置开机自启
sudo systemctl enable nginx
```

### 第九步：配置 SSL (HTTPS)

**使用 Let's Encrypt 免费证书**：

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 获取证书（自动配置 Nginx）
sudo certbot --nginx -d your-domain.com

# 证书会自动续期，测试续期
sudo certbot renew --dry-run
```

**Nginx 会自动更新配置，添加 HTTPS 支持和 HTTP 到 HTTPS 重定向。**

---

## 🔒 安全加固

### 1. 配置防火墙

```bash
# 安装 UFW
sudo apt install -y ufw

# 允许 SSH（重要！）
sudo ufw allow 22/tcp

# 允许 HTTP 和 HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable

# 查看状态
sudo ufw status
```

### 2. 限制数据库文件权限

```bash
sudo chmod 600 /opt/proxyadminpanel/proxy_admin.db
sudo chown proxyadmin:proxyadmin /opt/proxyadminpanel/proxy_admin.db
```

### 3. 配置 Fail2Ban（防止暴力破解）

```bash
# 安装 Fail2Ban
sudo apt install -y fail2ban

# 创建配置
sudo nano /etc/fail2ban/jail.local
```

**添加配置**：
```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
```

```bash
# 启动服务
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## 📊 监控和日志

### 查看应用日志

```bash
# Systemd 服务日志
sudo journalctl -u proxyadmin -f

# Nginx 访问日志
sudo tail -f /var/log/nginx/access.log

# Nginx 错误日志
sudo tail -f /var/log/nginx/error.log
```

### 配置日志轮转

```bash
# 创建日志轮转配置
sudo nano /etc/logrotate.d/proxyadmin
```

**内容**：
```
/var/log/proxyadmin/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 proxyadmin proxyadmin
    sharedscripts
    postrotate
        systemctl reload proxyadmin
    endscript
}
```

---

## 💾 自动备份

### 创建备份脚本

```bash
# 创建备份目录
sudo mkdir -p /opt/backups/proxyadmin

# 创建备份脚本
sudo nano /opt/proxyadminpanel/backup.sh
```

**备份脚本内容**：
```bash
#!/bin/bash

BACKUP_DIR="/opt/backups/proxyadmin"
DB_FILE="/opt/proxyadminpanel/proxy_admin.db"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/proxy_admin_${DATE}.db"

# 创建备份
cp $DB_FILE $BACKUP_FILE

# 压缩备份
gzip $BACKUP_FILE

# 删除 30 天前的备份
find $BACKUP_DIR -name "*.db.gz" -mtime +30 -delete

echo "Backup completed: ${BACKUP_FILE}.gz"
```

```bash
# 添加执行权限
sudo chmod +x /opt/proxyadminpanel/backup.sh

# 测试备份
sudo -u proxyadmin /opt/proxyadminpanel/backup.sh
```

### 配置自动备份（Cron）

```bash
# 编辑 crontab
sudo -u proxyadmin crontab -e
```

**添加定时任务**：
```
# 每天凌晨 2 点备份
0 2 * * * /opt/proxyadminpanel/backup.sh
```

---

## 🔄 更新和维护

### 更新应用

```bash
# 备份数据库
sudo -u proxyadmin /opt/proxyadminpanel/backup.sh

# 停止服务
sudo systemctl stop proxyadmin

# 更新代码（使用 git 或上传新文件）
cd /opt/proxyadminpanel
sudo -u proxyadmin git pull

# 更新依赖
sudo -u proxyadmin bash -c "source venv/bin/activate && pip install -r requirements.txt"

# 重新构建前端
cd frontend
sudo -u proxyadmin npm install
sudo -u proxyadmin npm run build

# 重启服务
sudo systemctl start proxyadmin
sudo systemctl restart nginx
```

### 查看系统资源

```bash
# 查看 CPU 和内存使用
htop

# 查看磁盘使用
df -h

# 查看服务状态
sudo systemctl status proxyadmin nginx
```

---

## 🐛 故障排查

### 后端无法启动

```bash
# 查看详细日志
sudo journalctl -u proxyadmin -n 100 --no-pager

# 检查端口占用
sudo ss -tlnp | grep :8000

# 手动测试启动
cd /opt/proxyadminpanel
sudo -u proxyadmin bash -c "source venv/bin/activate && python main.py"
```

### Nginx 配置错误

```bash
# 测试配置
sudo nginx -t

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 重新加载配置
sudo nginx -s reload
```

### 数据库问题

```bash
# 检查数据库文件
ls -la /opt/proxyadminpanel/proxy_admin.db

# 检查数据库完整性
sqlite3 /opt/proxyadminpanel/proxy_admin.db "PRAGMA integrity_check;"
```

### Core Service 连接失败

```bash
# 测试连接
curl -H "Auth: your-api-key" http://your-core-service/api/system/getInterFaces

# 检查网络连通性
ping your-core-service-ip

# 检查防火墙
sudo ufw status
```

---

## ✅ 部署完成检查清单

- [ ] 系统依赖安装完成
- [ ] Python 虚拟环境配置完成
- [ ] 数据库初始化成功
- [ ] 后端服务启动正常
- [ ] 前端构建成功
- [ ] Nginx 配置正确
- [ ] SSL 证书配置（如使用 HTTPS）
- [ ] 防火墙规则配置
- [ ] 能通过域名/IP 访问系统
- [ ] 能成功登录系统
- [ ] 核心功能测试通过
- [ ] 自动备份配置完成
- [ ] 日志轮转配置完成
- [ ] 监控配置（可选）

---

## 📞 技术支持

遇到问题请检查：
1. 系统日志：`sudo journalctl -u proxyadmin -f`
2. Nginx 日志：`/var/log/nginx/error.log`
3. 应用日志
4. 参考完整文档：`README.md`, `DEPLOYMENT.md`

---

**部署成功！享受你的代理管理系统吧！🎉**
