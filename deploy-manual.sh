#!/bin/bash

# Manual deployment script - Run this ON the Debian VM
# Copy this script to the VM and execute it

echo "🚀 Installing WireGuard VPN Manager..."

# Update system
echo "📦 Updating system packages..."
apt-get update

# Install dependencies
echo "📦 Installing dependencies..."
apt-get install -y python3 python3-pip python3-venv git wireguard wireguard-tools

# Create app directory
echo "📁 Creating application directory..."
mkdir -p /opt/wireguard-manager
cd /opt/wireguard-manager

# Clone repository
echo "📥 Cloning repository..."
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/ruhitrafian66/Linux-Wireguard-Configurator.git .
fi

# Create virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python packages..."
pip install -r requirements.txt

# Create config directory
echo "📁 Creating config directory..."
mkdir -p ~/.wireguard-configs

# Create systemd service
echo "⚙️  Creating systemd service..."
cat > /etc/systemd/system/wireguard-manager.service <<'SERVICE'
[Unit]
Description=WireGuard VPN Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/wireguard-manager
Environment="PATH=/opt/wireguard-manager/venv/bin"
ExecStart=/opt/wireguard-manager/venv/bin/python3 /opt/wireguard-manager/app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# Reload systemd and start service
echo "🔄 Starting service..."
systemctl daemon-reload
systemctl enable wireguard-manager
systemctl restart wireguard-manager

# Configure firewall if ufw is installed
if command -v ufw &> /dev/null; then
    echo "🔥 Configuring firewall..."
    ufw allow 5000/tcp
fi

echo ""
echo "✅ Deployment complete!"
echo "🌐 Access the app at: http://10.211.55.4:5000"
echo ""
echo "Service status:"
systemctl status wireguard-manager --no-pager
echo ""
echo "Useful commands:"
echo "  Check status: systemctl status wireguard-manager"
echo "  View logs:    journalctl -u wireguard-manager -f"
echo "  Restart:      systemctl restart wireguard-manager"
