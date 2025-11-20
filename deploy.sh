#!/bin/bash

# Deployment script for WireGuard VPN Manager
# Target: Debian VM at 10.211.55.4

VM_IP="10.211.55.4"
VM_USER="root"
VM_PASSWORD="root"
APP_DIR="/opt/wireguard-manager"
REPO_URL="https://github.com/ruhitrafian66/Linux-Wireguard-Configurator.git"

echo "🚀 Deploying WireGuard VPN Manager to $VM_IP..."

# Create deployment commands
DEPLOY_COMMANDS=$(cat <<'EOF'
# Update system
apt-get update

# Install dependencies
apt-get install -y python3 python3-pip python3-venv git wireguard wireguard-tools

# Create app directory
mkdir -p /opt/wireguard-manager
cd /opt/wireguard-manager

# Clone or update repository
if [ -d ".git" ]; then
    git pull
else
    git clone https://github.com/ruhitrafian66/Linux-Wireguard-Configurator.git .
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create config directory
mkdir -p ~/.wireguard-configs

# Create systemd service
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
systemctl daemon-reload
systemctl enable wireguard-manager
systemctl restart wireguard-manager

# Configure firewall if ufw is installed
if command -v ufw &> /dev/null; then
    ufw allow 5000/tcp
fi

echo "✅ Deployment complete!"
echo "🌐 Access the app at: http://10.211.55.4:5000"
systemctl status wireguard-manager --no-pager
EOF
)

# Deploy using SSH (with key authentication)
echo "📦 Connecting to VM and deploying..."
ssh -o StrictHostKeyChecking=no "$VM_USER@$VM_IP" "$DEPLOY_COMMANDS"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo "🌐 Access your WireGuard Manager at: http://$VM_IP:5000"
    echo ""
    echo "Useful commands:"
    echo "  Check status: ssh root@$VM_IP 'systemctl status wireguard-manager'"
    echo "  View logs:    ssh root@$VM_IP 'journalctl -u wireguard-manager -f'"
    echo "  Restart:      ssh root@$VM_IP 'systemctl restart wireguard-manager'"
else
    echo "❌ Deployment failed!"
    exit 1
fi
