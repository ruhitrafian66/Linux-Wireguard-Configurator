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

def parse_wg_config(config_path):
    """Extract relevant information from WireGuard config file"""
    info = {
        'name': config_path.stem,
        'address': None,
        'dns': None,
        'endpoint': None,
        'public_key': None
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
                
    except Exception as e:
        print(f"Error parsing config: {e}")
    
    return info

def get_connection_status():
    """Check if WireGuard is currently connected"""
    try:
        result = subprocess.run(['/usr/bin/wg', 'show'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            # Parse interface name
            lines = result.stdout.split('\n')
            if lines:
                interface = lines[0].split(':')[0].strip() if ':' in lines[0] else None
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
        # Disconnect first if connected
        subprocess.run(['/usr/bin/wg-quick', 'down', 'wg0'], capture_output=True, timeout=10)
        
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
            return jsonify({'success': False, 'error': result.stderr}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': 'Connection timeout'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/disconnect', methods=['POST'])
def disconnect():
    """Disconnect from VPN"""
    try:
        result = subprocess.run(
            ['/usr/bin/wg-quick', 'down', 'wg0'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0 or 'is not a WireGuard interface' in result.stderr:
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
        return jsonify({'success': True, 'message': 'Config uploaded successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
