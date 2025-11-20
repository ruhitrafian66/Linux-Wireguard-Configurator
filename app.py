#!/usr/bin/env python3
import os
import subprocess
import json
from flask import Flask, render_template, jsonify, request
from pathlib import Path
import configparser

app = Flask(__name__)

# Configuration
CONFIG_DIR = Path.home() / '.wireguard-configs'
CONFIG_DIR.mkdir(exist_ok=True)

def validate_wg_config(config_path):
    """Validate WireGuard config file"""
    try:
        with open(config_path, 'r') as f:
            content = f.read()
        
        # Check for placeholder/invalid keys
        if 'PrivateKey = *****' in content or 'PrivateKey = ' in content and 'PrivateKey = *' in content:
            return False, "Config contains placeholder PrivateKey (*****). Please use a valid WireGuard private key."
        
        # Check if PrivateKey exists
        has_private_key = False
        for line in content.split('\n'):
            if line.strip().startswith('PrivateKey'):
                has_private_key = True
                key = line.split('=', 1)[1].strip()
                # WireGuard keys are typically 44 characters (base64 encoded 32 bytes)
                # But allow 43-45 to handle edge cases with padding
                if len(key) < 40 or key == '*****' or '*' in key:
                    return False, f"Invalid PrivateKey format. Key appears to be placeholder or too short (got {len(key)} chars)."
        
        if not has_private_key:
            return False, "Config missing PrivateKey in [Interface] section."
        
        return True, None
    except Exception as e:
        return False, f"Error validating config: {str(e)}"

def get_autoconnect_config():
    """Get the current auto-connect configuration"""
    service_name = 'wg-autoconnect.service'
    try:
        result = subprocess.run(
            ['/usr/bin/systemctl', 'is-enabled', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0 and result.stdout.strip() == 'enabled':
            # Get the config name from the service file
            service_path = f'/etc/systemd/system/{service_name}'
            if os.path.exists(service_path):
                with open(service_path, 'r') as f:
                    content = f.read()
                    for line in content.split('\n'):
                        if 'ExecStart' in line and '.conf' in line:
                            config_path = line.split()[-1]
                            return Path(config_path).stem
            return True
        return None
    except Exception:
        return None

def parse_wg_config(config_path):
    """Extract relevant information from WireGuard config file"""
    info = {
        'name': config_path.stem,
        'address': None,
        'dns': None,
        'endpoint': None,
        'public_key': None,
        'autoconnect': False
    }
    
    try:
        with open(config_path, 'r') as f:
            content = f.read()
            
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('Address'):
                info['address'] = line.split('=')[1].strip()
            elif line.startswith('DNS'):
                info['dns'] = line.split('=')[1].strip()
            elif line.startswith('Endpoint'):
                info['endpoint'] = line.split('=')[1].strip()
            elif line.startswith('PublicKey') and info['public_key'] is None:
                info['public_key'] = line.split('=')[1].strip()[:20] + '...'
        
        # Check if this config is set for auto-connect
        autoconnect_config = get_autoconnect_config()
        if autoconnect_config == info['name']:
            info['autoconnect'] = True
                
    except Exception as e:
        print(f"Error parsing config: {e}")
    
    return info

def get_connection_status():
    """Check if WireGuard is currently connected"""
    try:
        result = subprocess.run(['/usr/bin/wg', 'show'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            # Parse interface name from output like "interface: wg2-NO-59"
            lines = result.stdout.split('\n')
            interface = None
            for line in lines:
                if line.startswith('interface:'):
                    interface = line.split(':', 1)[1].strip()
                    break
            if interface:
                return {'connected': True, 'interface': interface, 'details': result.stdout}
        return {'connected': False, 'interface': None, 'details': None}
    except Exception as e:
        return {'connected': False, 'interface': None, 'error': str(e)}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/configs', methods=['GET'])
def list_configs():
    """List all available WireGuard config files"""
    configs = []
    for config_file in CONFIG_DIR.glob('*.conf'):
        info = parse_wg_config(config_file)
        configs.append(info)
    
    # Sort by name
    configs.sort(key=lambda x: x['name'])
    return jsonify(configs)

@app.route('/api/status', methods=['GET'])
def status():
    """Get current VPN connection status"""
    return jsonify(get_connection_status())

@app.route('/api/connect', methods=['POST'])
def connect():
    """Connect to VPN using specified config"""
    data = request.json
    config_name = data.get('config')
    
    if not config_name:
        return jsonify({'success': False, 'error': 'No config specified'}), 400
    
    config_path = CONFIG_DIR / f"{config_name}.conf"
    if not config_path.exists():
        return jsonify({'success': False, 'error': 'Config not found'}), 404
    
    try:
        # Validate config first
        is_valid, error_msg = validate_wg_config(config_path)
        if not is_valid:
            return jsonify({'success': False, 'error': error_msg}), 400
        
        # Ensure proper permissions
        os.chmod(config_path, 0o600)
        
        # Get current connections and disconnect them
        status = get_connection_status()
        if status['connected'] and status['interface']:
            subprocess.run(['/usr/bin/wg-quick', 'down', status['interface']], 
                         capture_output=True, timeout=10)
        
        # Connect with new config
        result = subprocess.run(
            ['/usr/bin/wg-quick', 'up', str(config_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Connected successfully'})
        else:
            error_msg = result.stderr if result.stderr else result.stdout
            return jsonify({'success': False, 'error': error_msg}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Connection timeout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from VPN"""
    try:
        # Get current interface name
        status = get_connection_status()
        if not status['connected'] or not status['interface']:
            return jsonify({'success': True, 'message': 'Already disconnected'})
        
        interface = status['interface']
        
        # Use wg-quick save to preserve state, then bring down interface
        # First try to find the original config
        config_path = CONFIG_DIR / f"{interface}.conf"
        
        if config_path.exists():
            # Use wg-quick down with the full config path
            result = subprocess.run(
                ['/usr/bin/wg-quick', 'down', str(config_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # Fallback: manually bring down the interface
            subprocess.run(['/usr/bin/ip', 'link', 'set', interface, 'down'], 
                         capture_output=True, timeout=5)
            result = subprocess.run(
                ['/usr/bin/ip', 'link', 'delete', interface],
                capture_output=True,
                text=True,
                timeout=10
            )
        
        if result.returncode == 0 or 'Cannot find device' in result.stderr:
            return jsonify({'success': True, 'message': 'Disconnected successfully'})
        else:
            return jsonify({'success': False, 'error': result.stderr}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_config():
    """Upload a new WireGuard config file"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.conf'):
        return jsonify({'success': False, 'error': 'File must be a .conf file'}), 400
    
    try:
        filepath = CONFIG_DIR / file.filename
        file.save(filepath)
        # Set proper permissions (0600 = rw-------)
        os.chmod(filepath, 0o600)
        
        # Validate the uploaded config
        is_valid, error_msg = validate_wg_config(filepath)
        if not is_valid:
            return jsonify({'success': False, 'error': f'Config uploaded but invalid: {error_msg}'}), 400
        
        return jsonify({'success': True, 'message': 'Config uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoconnect', methods=['POST'])
def set_autoconnect():
    """Enable or disable auto-connect on reboot for a specific config"""
    data = request.json
    config_name = data.get('config')
    enabled = data.get('enabled', False)
    
    if not config_name:
        return jsonify({'success': False, 'error': 'No config specified'}), 400
    
    config_path = CONFIG_DIR / f"{config_name}.conf"
    if not config_path.exists():
        return jsonify({'success': False, 'error': 'Config not found'}), 404
    
    service_name = 'wg-autoconnect.service'
    service_path = f'/etc/systemd/system/{service_name}'
    
    try:
        if enabled:
            # Create systemd service for auto-connect
            service_content = f"""[Unit]
Description=WireGuard Auto-Connect ({config_name})
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/wg-quick up {config_path}
RemainAfterExit=yes
ExecStop=/usr/bin/wg-quick down {config_path.stem}

[Install]
WantedBy=multi-user.target
"""
            with open(service_path, 'w') as f:
                f.write(service_content)
            
            # Reload systemd and enable service
            subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=True, timeout=5)
            subprocess.run(['/usr/bin/systemctl', 'enable', service_name], check=True, timeout=5)
            
            return jsonify({'success': True, 'message': f'Auto-connect enabled for {config_name}'})
        else:
            # Disable and remove service
            subprocess.run(['/usr/bin/systemctl', 'disable', service_name], 
                         capture_output=True, timeout=5)
            subprocess.run(['/usr/bin/systemctl', 'stop', service_name], 
                         capture_output=True, timeout=5)
            
            if os.path.exists(service_path):
                os.remove(service_path)
            
            subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=True, timeout=5)
            
            return jsonify({'success': True, 'message': 'Auto-connect disabled'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
