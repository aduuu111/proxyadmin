# 部署说明 / Deployment Guide

## 一键安装 / Quick Installation

在 Debian/Ubuntu 系统上执行以下命令：

```bash
wget http://47.129.171.69/downloads/xui.sh && chmod 777 xui.sh && ./xui.sh
```

## 安装后配置 / Post-Installation Configuration

### 1. 配置核心服务连接

编辑配置文件：
```bash
nano /etc/proxyadmin/core_config.ini
```

修改以下内容：
```ini
[core_service]
api_url = http://your-core-service-ip:port
api_key = your-api-key
timeout = 10
```

### 2. 重启服务

```bash
systemctl restart proxyadmin
```

### 3. 访问面板

浏览器访问：`http://your-server-ip`

默认账号：
- 用户名：admin
- 密码：admin

**⚠️ 首次登录后请立即修改密码！**

## 服务管理

```bash
# 查看日志
journalctl -u proxyadmin -f

# 重启服务
systemctl restart proxyadmin

# 停止服务
systemctl stop proxyadmin

# 查看状态
systemctl status proxyadmin
```

## 文件位置

- 安装目录：`/opt/proxyadmin`
- 配置文件：`/etc/proxyadmin/core_config.ini`
- 数据库：`/opt/proxyadmin/proxy_admin.db`
- 服务文件：`/etc/systemd/system/proxyadmin.service`
