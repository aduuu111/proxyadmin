#!/bin/bash
#
# ProxyAdminPanel Installation Script
# For Debian/Ubuntu Linux
#
# Usage: wget http://47.129.171.69/downloads/xui.sh && chmod 777 xui.sh && ./xui.sh
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
INSTALL_DIR="/opt/proxyadmin"
SERVICE_NAME="proxyadmin"
REPO_URL="https://github.com/yourusername/proxyadmin.git"  # Update this with your repo
DOWNLOAD_URL="http://47.129.171.69/downloads/proxyadmin.tar.gz"
USE_GIT=true  # Set to false to use download URL instead

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}ProxyAdminPanel Installer${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
else
    echo -e "${RED}Error: Cannot detect OS${NC}"
    exit 1
fi

if [[ "$OS" != "ubuntu" && "$OS" != "debian" ]]; then
    echo -e "${RED}Error: This script only supports Ubuntu/Debian${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS${NC}"
echo ""

# Update system
echo -e "${YELLOW}Updating system packages...${NC}"
apt-get update -qq

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
apt-get install -y -qq \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    curl \
    wget \
    git \
    sqlite3

# Install Node.js 18.x
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}Installing Node.js...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
    apt-get install -y -qq nodejs
fi

echo -e "${GREEN}Node.js version: $(node --version)${NC}"
echo -e "${GREEN}npm version: $(npm --version)${NC}"

# Create installation directory
echo -e "${YELLOW}Creating installation directory...${NC}"
mkdir -p $INSTALL_DIR
cd $INSTALL_DIR

# Download and extract project
echo -e "${YELLOW}Downloading project files...${NC}"
if [ "$USE_GIT" = true ]; then
    echo -e "${YELLOW}Cloning from Git repository...${NC}"
    git clone $REPO_URL .
else
    echo -e "${YELLOW}Downloading from URL...${NC}"
    wget -q $DOWNLOAD_URL -O proxyadmin.tar.gz
    tar -xzf proxyadmin.tar.gz
    rm proxyadmin.tar.gz
fi

# Create Python virtual environment
echo -e "${YELLOW}Setting up Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Build frontend
echo -e "${YELLOW}Building frontend...${NC}"
cd frontend
npm install --silent
npm run build
cd ..

# Create config directory
echo -e "${YELLOW}Setting up configuration...${NC}"
mkdir -p /etc/proxyadmin

# Copy core config if not exists
if [ ! -f /etc/proxyadmin/core_config.ini ]; then
    cp core_config.ini /etc/proxyadmin/core_config.ini
    echo -e "${YELLOW}Configuration file created at: /etc/proxyadmin/core_config.ini${NC}"
    echo -e "${YELLOW}Please edit this file to configure your core service connection${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python init_db.py

# Install systemd service
echo -e "${YELLOW}Installing systemd service...${NC}"
cp proxyadmin.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable $SERVICE_NAME
systemctl start $SERVICE_NAME

# Configure Nginx
echo -e "${YELLOW}Configuring Nginx...${NC}"
cat > /etc/nginx/sites-available/proxyadmin <<'EOF'
server {
    listen 80;
    server_name _;

    # Frontend
    location / {
        root /opt/proxyadmin/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# Enable Nginx site
ln -sf /etc/nginx/sites-available/proxyadmin /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl restart nginx

# Set permissions
chmod 600 /etc/proxyadmin/core_config.ini
chown -R root:root $INSTALL_DIR

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Installation Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "${GREEN}Service Status:${NC}"
systemctl status $SERVICE_NAME --no-pager | head -n 10
echo ""
echo -e "${GREEN}Access the panel at: http://$(hostname -I | awk '{print $1}')${NC}"
echo -e "${GREEN}Default credentials:${NC}"
echo -e "  Username: ${YELLOW}admin${NC}"
echo -e "  Password: ${YELLOW}admin${NC}"
echo ""
echo -e "${YELLOW}IMPORTANT:${NC}"
echo -e "1. Edit core service config: ${YELLOW}/etc/proxyadmin/core_config.ini${NC}"
echo -e "2. Change default admin password after first login"
echo -e "3. Restart service after config changes: ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
echo ""
echo -e "${GREEN}Useful commands:${NC}"
echo -e "  View logs: ${YELLOW}journalctl -u $SERVICE_NAME -f${NC}"
echo -e "  Restart service: ${YELLOW}systemctl restart $SERVICE_NAME${NC}"
echo -e "  Stop service: ${YELLOW}systemctl stop $SERVICE_NAME${NC}"
echo ""
