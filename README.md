# WireGuard VPN Manager

A simple web-based frontend for managing WireGuard VPN connections on Linux.

## Features

- 🔌 Connect and disconnect to VPN using config files
- 📊 Real-time connection status monitoring
- 📁 Upload and manage WireGuard configuration files
- 📋 Extract and display relevant information from config files
- 🎨 Clean, modern web interface

## Prerequisites

- Linux system with WireGuard installed
- Python 3.7+
- sudo privileges (for WireGuard operations)

## Installation

1. Install WireGuard (if not already installed):
```bash
# Ubuntu/Debian
sudo apt install wireguard

# Fedora
sudo dnf install wireguard-tools

# Arch
sudo pacman -S wireguard-tools
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Setup

1. Configure sudo permissions for WireGuard (to avoid password prompts):
```bash
sudo visudo
```

Add this line (replace `username` with your username):
```
username ALL=(ALL) NOPASSWD: /usr/bin/wg-quick
```

2. Place your WireGuard config files in `~/.wireguard-configs/` or upload them through the web interface.

## Usage

1. Start the server:
```bash
python3 app.py
```

2. Open your browser and navigate to:
```
http://localhost:5000
```

Or from another device on your network:
```
http://YOUR_SERVER_IP:5000
```

3. Upload your WireGuard `.conf` files or place them in `~/.wireguard-configs/`

4. Click on any configuration to connect

5. Use the Disconnect button to disconnect

## Configuration Files

Config files should be standard WireGuard configuration files (`.conf`). The app will extract and display:
- Interface Address
- DNS servers
- Peer Endpoint
- Public Key

Example config structure:
```ini
[Interface]
PrivateKey = YOUR_PRIVATE_KEY
Address = 10.0.0.2/24
DNS = 1.1.1.1

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = vpn.example.com:51820
AllowedIPs = 0.0.0.0/0
```

## Security Notes

- This app requires sudo privileges to manage WireGuard connections
- Run it only on trusted networks (home server)
- Consider adding authentication if exposing to the internet
- Config files are stored in `~/.wireguard-configs/`

## Troubleshooting

**Connection fails:**
- Ensure WireGuard is installed: `wg --version`
- Check sudo permissions are configured correctly
- Verify config file format is correct

**Can't access from other devices:**
- Check firewall settings: `sudo ufw allow 5000`
- Ensure the server is running on `0.0.0.0` (not `127.0.0.1`)

## License

MIT
