let currentStatus = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadConfigs();
    updateStatus();
    
    // Auto-refresh status every 5 seconds
    setInterval(updateStatus, 5000);
    
    // Event listeners
    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadConfigs();
        updateStatus();
    });
    
    document.getElementById('disconnect-btn').addEventListener('click', disconnect);
    document.getElementById('file-upload').addEventListener('change', handleFileUpload);
});

async function loadConfigs() {
    const configList = document.getElementById('config-list');
    configList.innerHTML = '<p class="loading">Loading configurations...</p>';
    
    try {
        const response = await fetch('/api/configs');
        const configs = await response.json();
        
        if (configs.length === 0) {
            configList.innerHTML = '<p class="loading">No configurations found. Upload a .conf file to get started.</p>';
            return;
        }
        
        configList.innerHTML = '';
        configs.forEach(config => {
            const card = createConfigCard(config);
            configList.appendChild(card);
        });
    } catch (error) {
        configList.innerHTML = '<p class="loading">Error loading configurations</p>';
        showNotification('Failed to load configurations', 'error');
    }
}

function createConfigCard(config) {
    const card = document.createElement('div');
    card.className = 'config-card';
    
    const cardContent = document.createElement('div');
    cardContent.className = 'config-card-content';
    cardContent.onclick = () => connect(config.name);
    
    cardContent.innerHTML = `
        <h3>${config.name}</h3>
        <div class="config-info">
            ${config.address ? `<div class="config-info-item"><strong>Address:</strong><span>${config.address}</span></div>` : ''}
            ${config.endpoint ? `<div class="config-info-item"><strong>Endpoint:</strong><span>${config.endpoint}</span></div>` : ''}
            ${config.dns ? `<div class="config-info-item"><strong>DNS:</strong><span>${config.dns}</span></div>` : ''}
            ${config.public_key ? `<div class="config-info-item"><strong>Public Key:</strong><span>${config.public_key}</span></div>` : ''}
        </div>
    `;
    
    // Add auto-connect toggle
    const autoconnectDiv = document.createElement('div');
    autoconnectDiv.className = 'autoconnect-toggle';
    autoconnectDiv.onclick = (e) => e.stopPropagation();
    
    autoconnectDiv.innerHTML = `
        <label class="toggle-label">
            <input type="checkbox" id="autoconnect-${config.name}" ${config.autoconnect ? 'checked' : ''}>
            <span class="toggle-slider"></span>
            <span class="toggle-text">Auto-connect on reboot</span>
        </label>
    `;
    
    card.appendChild(cardContent);
    card.appendChild(autoconnectDiv);
    
    // Add event listener for toggle
    setTimeout(() => {
        const checkbox = document.getElementById(`autoconnect-${config.name}`);
        if (checkbox) {
            checkbox.addEventListener('change', (e) => {
                toggleAutoconnect(config.name, e.target.checked);
            });
        }
    }, 0);
    
    return card;
}

async function toggleAutoconnect(configName, enabled) {
    try {
        const response = await fetch('/api/autoconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: configName, enabled: enabled })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(result.message, 'success');
            loadConfigs();
        } else {
            showNotification('Failed to update auto-connect: ' + result.error, 'error');
            loadConfigs();
        }
    } catch (error) {
        showNotification('Failed to update auto-connect: ' + error.message, 'error');
        loadConfigs();
    }
}

async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const status = await response.json();
        currentStatus = status;
        
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        const disconnectBtn = document.getElementById('disconnect-btn');
        const connectionDetails = document.getElementById('connection-details');
        const connectionInfo = document.getElementById('connection-info');
        
        if (status.connected) {
            statusIndicator.className = 'status connected';
            statusText.textContent = `Connected${status.interface ? ' (' + status.interface + ')' : ''}`;
            disconnectBtn.disabled = false;
            
            if (status.details) {
                connectionDetails.style.display = 'block';
                connectionInfo.textContent = status.details;
            }
        } else {
            statusIndicator.className = 'status disconnected';
            statusText.textContent = 'Disconnected';
            disconnectBtn.disabled = true;
            connectionDetails.style.display = 'none';
        }
    } catch (error) {
        console.error('Failed to update status:', error);
    }
}

async function connect(configName) {
    if (currentStatus && currentStatus.connected) {
        if (!confirm('Already connected. Disconnect and connect to this configuration?')) {
            return;
        }
    }
    
    try {
        const response = await fetch('/api/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ config: configName })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Connected successfully!', 'success');
            updateStatus();
        } else {
            showNotification('Connection failed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Connection failed: ' + error.message, 'error');
    }
}

async function disconnect() {
    try {
        const response = await fetch('/api/disconnect', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Disconnected successfully!', 'success');
            updateStatus();
        } else {
            showNotification('Disconnect failed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Disconnect failed: ' + error.message, 'error');
    }
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Config uploaded successfully!', 'success');
            loadConfigs();
        } else {
            showNotification('Upload failed: ' + result.error, 'error');
        }
    } catch (error) {
        showNotification('Upload failed: ' + error.message, 'error');
    }
    
    // Reset file input
    event.target.value = '';
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type} show`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}
