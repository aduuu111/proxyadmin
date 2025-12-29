# ProxyAdminPanel

A modern web-based proxy management panel with X-UI style interface.

## Features

- User management with traffic and bandwidth limits
- Multiple outbound protocols (Direct, SOCKS5, HTTP, Shadowsocks)
- Traffic routing rules with priority
- Real-time dashboard with system statistics
- JWT authentication for admin panel
- API key authentication for external integrations
- Batch operations support

## Quick Installation (Debian/Ubuntu)

```bash
wget https://raw.githubusercontent.com/aduuu111/proxyadmin/main/xui.sh && chmod +x xui.sh && sudo ./xui.sh
```

## Configuration

### Core Service Configuration

Edit `/etc/proxyadmin/core_config.ini`:

```ini
[core_service]
# Core Service API Endpoint
api_url = http://124.243.137.203:51128

# Core Service API Key
api_key = 123123

# Request Timeout (seconds)
timeout = 10
```

After changing configuration, restart the service:
```bash
systemctl restart proxyadmin
```

## Default Credentials

- Username: `admin`
- Password: `admin`

**⚠️ Change the default password immediately after first login!**

## Service Management

```bash
# View logs
journalctl -u proxyadmin -f

# Restart service
systemctl restart proxyadmin

# Stop service
systemctl stop proxyadmin

# Check status
systemctl status proxyadmin
```

## API Documentation

Access the interactive API documentation at:
- Swagger UI: `http://your-server/docs`
- ReDoc: `http://your-server/redoc`
