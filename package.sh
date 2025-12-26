#!/bin/bash
# Package script for Linux deployment
# Run this on a Linux machine or WSL

echo "Creating deployment package..."

# Create temporary directory
mkdir -p /tmp/proxyadmin-package
cd /tmp/proxyadmin-package

# Copy project files (excluding unnecessary files)
rsync -av --exclude='node_modules' \
          --exclude='venv' \
          --exclude='*.db' \
          --exclude='*.sqlite' \
          --exclude='__pycache__' \
          --exclude='.git' \
          --exclude='frontend/dist' \
          --exclude='*.log' \
          --exclude='.vscode' \
          --exclude='.idea' \
          "$OLDPWD/" .

# Create tarball
tar -czf proxyadmin.tar.gz *

# Move to original directory
mv proxyadmin.tar.gz "$OLDPWD/"

# Cleanup
cd "$OLDPWD"
rm -rf /tmp/proxyadmin-package

echo "Package created: proxyadmin.tar.gz"
echo "Upload this file to your server at: /var/www/downloads/"
