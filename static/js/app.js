// Global state
let isRunning = false;
let updateInterval = null;
let lastStats = { wifi: {}, internet: {} };

// Channel definitions
const CHANNELS = {
    '2.4': [
        { value: '1', label: '1 (2.412 GHz)' },
        { value: '2', label: '2 (2.417 GHz)' },
        { value: '3', label: '3 (2.422 GHz)' },
        { value: '4', label: '4 (2.427 GHz)' },
        { value: '5', label: '5 (2.432 GHz)' },
        { value: '6', label: '6 (2.437 GHz)' },
        { value: '7', label: '7 (2.442 GHz)' },
        { value: '8', label: '8 (2.447 GHz)' },
        { value: '9', label: '9 (2.452 GHz)' },
        { value: '10', label: '10 (2.457 GHz)' },
        { value: '11', label: '11 (2.462 GHz)' },
        { value: '12', label: '12 (2.467 GHz)' },
        { value: '13', label: '13 (2.472 GHz)' }
    ],
    '5': [
        { value: '36', label: '36 (5.180 GHz)' },
        { value: '40', label: '40 (5.200 GHz)' },
        { value: '44', label: '44 (5.220 GHz)' },
        { value: '48', label: '48 (5.240 GHz)' },
        { value: '52', label: '52 (5.260 GHz)' },
        { value: '56', label: '56 (5.280 GHz)' },
        { value: '60', label: '60 (5.300 GHz)' },
        { value: '64', label: '64 (5.320 GHz)' },
        { value: '100', label: '100 (5.500 GHz)' },
        { value: '104', label: '104 (5.520 GHz)' },
        { value: '108', label: '108 (5.540 GHz)' },
        { value: '112', label: '112 (5.560 GHz)' },
        { value: '116', label: '116 (5.580 GHz)' },
        { value: '120', label: '120 (5.600 GHz)' },
        { value: '124', label: '124 (5.620 GHz)' },
        { value: '128', label: '128 (5.640 GHz)' },
        { value: '132', label: '132 (5.660 GHz)' },
        { value: '136', label: '136 (5.680 GHz)' },
        { value: '140', label: '140 (5.700 GHz)' },
        { value: '144', label: '144 (5.720 GHz)' },
        { value: '149', label: '149 (5.745 GHz)' },
        { value: '153', label: '153 (5.765 GHz)' },
        { value: '157', label: '157 (5.785 GHz)' },
        { value: '161', label: '161 (5.805 GHz)' },
        { value: '165', label: '165 (5.825 GHz)' }
    ]
};

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    init();
});

// Initialize application
async function init() {
    await loadInterfaces();
    
    // Initialize channel list for default frequency (2.4 GHz)
    updateChannelList('2.4');
    
    await checkStatus();
    await loadLastConfig();
    setupEventListeners();
    addLog('WiFi Hotspot Manager initialized', 'success');
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startHotspot);
    document.getElementById('stopBtn').addEventListener('click', stopHotspot);
    document.getElementById('loadLastConfig').addEventListener('click', loadLastConfig);
    document.getElementById('toggleAdvanced').addEventListener('click', toggleAdvancedSettings);
    document.getElementById('toggleWifiCapab').addEventListener('click', toggleWifiCapabilities);
    document.getElementById('viewConfig').addEventListener('click', viewHostapdConfig);
    
    // Update command preview on any input change
    const formElements = document.querySelectorAll('#configForm input, #configForm select');
    formElements.forEach(element => {
        element.addEventListener('change', () => {
            // No command preview needed for hostapd mode
        });
        element.addEventListener('input', () => {
            // No command preview needed for hostapd mode
        });
    });
    
    // Disable internet interface when noInternet is checked
    document.getElementById('noInternet').addEventListener('change', (e) => {
        document.getElementById('internetInterface').disabled = e.target.checked;
    });
    
    // Update channel list when frequency band changes
    document.getElementById('freqBand').addEventListener('change', (e) => {
        updateChannelList(e.target.value);
    });
    
    // Auto-enable 802.11n when 802.11ac is enabled (ac requires n)
    document.getElementById('ieee80211ac').addEventListener('change', (e) => {
        if (e.target.checked) {
            document.getElementById('ieee80211n').checked = true;
            
            // Also check if 5GHz is selected
            const freqBand = document.getElementById('freqBand').value;
            if (freqBand !== '5') {
                if (confirm('802.11ac requires 5 GHz frequency band. Switch to 5 GHz?')) {
                    document.getElementById('freqBand').value = '5';
                    updateChannelList('5');
                }
            }
        }
    });
    
    // Auto-enable 802.11n when 802.11ax is enabled
    document.getElementById('ieee80211ax').addEventListener('change', (e) => {
        if (e.target.checked) {
            document.getElementById('ieee80211n').checked = true;
        }
    });
}

// Update channel list based on frequency band
function updateChannelList(freqBand) {
    const channelSelect = document.getElementById('channel');
    const currentValue = channelSelect.value;
    
    channelSelect.innerHTML = '';
    
    const channels = CHANNELS[freqBand] || CHANNELS['2.4'];
    
    channels.forEach(channel => {
        const option = document.createElement('option');
        option.value = channel.value;
        option.textContent = channel.label;
        channelSelect.appendChild(option);
    });
    
    // Try to restore previous value if it exists in new list
    const hasCurrentValue = Array.from(channelSelect.options).some(opt => opt.value === currentValue);
    if (hasCurrentValue) {
        channelSelect.value = currentValue;
    } else {
        // Set default based on band
        channelSelect.value = freqBand === '5' ? '36' : '6';
    }
}

// Toggle advanced settings
function toggleAdvancedSettings() {
    const advancedSettings = document.getElementById('advancedSettings');
    const toggleBtn = document.getElementById('toggleAdvanced');
    
    if (advancedSettings.style.display === 'none') {
        advancedSettings.style.display = 'block';
        toggleBtn.textContent = 'Hide';
    } else {
        advancedSettings.style.display = 'none';
        toggleBtn.textContent = 'Show';
    }
}

// Toggle WiFi capabilities section
function toggleWifiCapabilities() {
    const wifiCapabSettings = document.getElementById('wifiCapabSettings');
    const toggleBtn = document.getElementById('toggleWifiCapab');
    
    if (wifiCapabSettings.style.display === 'none') {
        wifiCapabSettings.style.display = 'block';
        toggleBtn.textContent = 'Hide';
    } else {
        wifiCapabSettings.style.display = 'none';
        toggleBtn.textContent = 'Show';
    }
}

// View hostapd configuration
async function viewHostapdConfig() {
    try {
        const response = await fetch('/api/hostapd-config');
        const data = await response.json();
        
        if (data.config) {
            // Create modal
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.8); z-index: 9999;
                display: flex; align-items: center; justify-content: center;
                padding: 20px;
            `;
            
            modal.innerHTML = `
                <div style="background: white; border-radius: 12px; padding: 24px; max-width: 800px; width: 100%; max-height: 80vh; overflow: auto;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
                        <h2 style="margin: 0;">hostapd.conf</h2>
                        <button onclick="this.closest('div').parentElement.remove()" style="background: none; border: none; font-size: 24px; cursor: pointer; color: #718096;">&times;</button>
                    </div>
                    <pre style="background: #1a202c; color: #68d391; padding: 16px; border-radius: 8px; overflow-x: auto; margin: 0; font-size: 13px; line-height: 1.5;">${escapeHtml(data.config)}</pre>
                    <button onclick="this.closest('div').parentElement.remove()" style="margin-top: 16px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">Close</button>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Close on background click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.remove();
                }
            });
        } else {
            alert('No configuration file found. Start the hotspot first.');
        }
    } catch (error) {
        alert('Error loading configuration: ' + error.message);
        addLog('Error loading config: ' + error.message, 'error');
    }
}

// Escape HTML for display
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Load network interfaces
async function loadInterfaces() {
    try {
        const response = await fetch('/api/interfaces');
        const data = await response.json();
        
        const wifiSelect = document.getElementById('wifiInterface');
        const ethSelect = document.getElementById('internetInterface');
        
        wifiSelect.innerHTML = '';
        ethSelect.innerHTML = '';
        
        let wifiFound = false;
        let ethFound = false;
        
        data.interfaces.forEach(iface => {
            const option = document.createElement('option');
            option.value = iface.name;
            
            // Show interface info
            let info = iface.name;
            if (iface.supportsAP) info += ' ✓ AP';
            if (!iface.isWireless && iface.type === 'ethernet') info += ' (Ethernet)';
            
            option.textContent = info;
            
            if (iface.isWireless && iface.supportsAP) {
                wifiSelect.appendChild(option);
                wifiFound = true;
            } else if (iface.type === 'ethernet') {
                ethSelect.appendChild(option);
                ethFound = true;
            }
        });
        
        // Add fallback options if no interfaces found
        if (!wifiFound) {
            const option = document.createElement('option');
            option.value = 'wlan0';
            option.textContent = 'wlan0 (default)';
            wifiSelect.appendChild(option);
        }
        
        if (!ethFound) {
            const option = document.createElement('option');
            option.value = 'eth0';
            option.textContent = 'eth0 (default)';
            ethSelect.appendChild(option);
        }
        
        addLog(`Loaded ${data.interfaces.length} network interfaces`);
    } catch (error) {
        console.error('Error loading interfaces:', error);
        addLog(`Error loading interfaces: ${error.message}`, 'error');
    }
}

// Check current status
async function checkStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        if (data.status.isRunning) {
            setRunningState(true);
            startUpdates();
            
            // Restore config to form
            if (data.status.config) {
                restoreConfig(data.status.config);
                updateCurrentConfigDisplay(data.status.config);
            }
            
            addLog('Restored connection to running hotspot', 'success');
        }
    } catch (error) {
        console.error('Error checking status:', error);
    }
}

// Load last configuration
async function loadLastConfig() {
    try {
        const response = await fetch('/api/last-config');
        const data = await response.json();
        
        if (data.config) {
            restoreConfig(data.config);
            addLog('Loaded last configuration', 'success');
        } else {
            addLog('No saved configuration found', 'warning');
        }
    } catch (error) {
        console.error('Error loading last config:', error);
        addLog(`Error loading config: ${error.message}`, 'error');
    }
}

// Restore configuration to form
function restoreConfig(config) {
    // Restore frequency band FIRST (before channel)
    if (config.freqBand) {
        document.getElementById('freqBand').value = config.freqBand;
        updateChannelList(config.freqBand);
    }
    
    // Basic settings
    if (config.wifiInterface) document.getElementById('wifiInterface').value = config.wifiInterface;
    if (config.internetInterface) document.getElementById('internetInterface').value = config.internetInterface;
    if (config.ssid) document.getElementById('ssid').value = config.ssid;
    if (config.password) document.getElementById('password').value = config.password;
    if (config.wpaVersion) document.getElementById('wpaVersion').value = config.wpaVersion;
    
    // Set channel AFTER frequency band is set
    if (config.channel) {
        const channelSelect = document.getElementById('channel');
        const hasChannel = Array.from(channelSelect.options).some(opt => opt.value === config.channel);
        if (hasChannel) {
            channelSelect.value = config.channel;
        }
    }
    
    // Advanced settings
    if (config.country) document.getElementById('country').value = config.country;
    if (config.gateway) document.getElementById('gateway').value = config.gateway;
    if (config.dhcpDns) document.getElementById('dhcpDns').value = config.dhcpDns;
    if (config.driver) document.getElementById('driver').value = config.driver;
    if (config.dhcpStart) document.getElementById('dhcpStart').value = config.dhcpStart;
    if (config.dhcpEnd) document.getElementById('dhcpEnd').value = config.dhcpEnd;
    if (config.leaseTime) document.getElementById('leaseTime').value = config.leaseTime;
    if (config.maxStations) document.getElementById('maxStations').value = config.maxStations;
    if (config.htCapab) document.getElementById('htCapab').value = config.htCapab;
    if (config.vhtCapab) document.getElementById('vhtCapab').value = config.vhtCapab;
    if (config.heCapab && document.getElementById('heCapab')) {
        document.getElementById('heCapab').value = config.heCapab;
    }
    if (config.macFilterAccept) document.getElementById('macFilterAccept').value = config.macFilterAccept;
    if (config.hostsFile) document.getElementById('hostsFile').value = config.hostsFile;
    
    // Checkboxes
    document.getElementById('ieee80211n').checked = config.ieee80211n || false;
    document.getElementById('ieee80211ac').checked = config.ieee80211ac || false;
    if (document.getElementById('ieee80211ax')) {
        document.getElementById('ieee80211ax').checked = config.ieee80211ax || false;
    }
    document.getElementById('hidden').checked = config.hidden || false;
    document.getElementById('isolate').checked = config.isolate || false;
    document.getElementById('macFilter').checked = config.macFilter || false;
    document.getElementById('noInternet').checked = config.noInternet || false;
    document.getElementById('noDns').checked = config.noDns || false;
    document.getElementById('noDnsmasq').checked = config.noDnsmasq || false;
    document.getElementById('psk').checked = config.psk || false;
}

// Get configuration from form
function getConfig() {
    const config = {
        wifiInterface: document.getElementById('wifiInterface').value,
        ssid: document.getElementById('ssid').value,
        password: document.getElementById('password').value,
        wpaVersion: document.getElementById('wpaVersion').value,
        channel: document.getElementById('channel').value,
        freqBand: document.getElementById('freqBand').value,
        country: document.getElementById('country').value.toUpperCase(),
        gateway: document.getElementById('gateway').value || '192.168.12.1',
        dhcpDns: document.getElementById('dhcpDns').value || '8.8.8.8,8.8.4.4',
        driver: document.getElementById('driver').value || 'nl80211',
        
        // DHCP settings
        dhcpStart: document.getElementById('dhcpStart').value || '192.168.12.10',
        dhcpEnd: document.getElementById('dhcpEnd').value || '192.168.12.100',
        leaseTime: document.getElementById('leaseTime').value || '12h',
        maxStations: document.getElementById('maxStations').value,
        
        // WiFi standards
        ieee80211n: document.getElementById('ieee80211n').checked,
        ieee80211ac: document.getElementById('ieee80211ac').checked,
        ieee80211ax: document.getElementById('ieee80211ax')?.checked || false,
        
        // Capabilities
        htCapab: document.getElementById('htCapab').value,
        vhtCapab: document.getElementById('vhtCapab').value,
        heCapab: document.getElementById('heCapab')?.value,
        
        // Other options
        hidden: document.getElementById('hidden').checked,
        isolate: document.getElementById('isolate').checked,
        macFilter: document.getElementById('macFilter').checked,
        macFilterAccept: document.getElementById('macFilterAccept').value,
        hostsFile: document.getElementById('hostsFile').value,
        noInternet: document.getElementById('noInternet').checked,
        noDns: document.getElementById('noDns').checked,
        noDnsmasq: document.getElementById('noDnsmasq').checked,
        psk: document.getElementById('psk').checked
    };
    
    if (!config.noInternet) {
        config.internetInterface = document.getElementById('internetInterface').value;
    }
    
    return config;
}

// Start hotspot
async function startHotspot() {
    const config = getConfig();
    
    // Validation
    if (!config.ssid) {
        alert('Please enter an SSID');
        return;
    }
    
    if (config.password && config.password.length < 8 && !config.psk) {
        alert('Password must be at least 8 characters (or use PSK mode)');
        return;
    }
    
    if (config.psk && config.password && config.password.length !== 64) {
        alert('PSK mode requires exactly 64 hexadecimal characters');
        return;
    }
    
    // Validate 802.11ac on 5GHz
    if (config.ieee80211ac && config.freqBand !== '5') {
        alert('802.11ac requires 5 GHz frequency band');
        return;
    }
    
    try {
        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = true;
        startBtn.innerHTML = '<span class="loading"></span> Starting...';
        
        addLog(`Starting hotspot: ${config.ssid}...`);
        
        const response = await fetch('/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(config)
        });
        
        const data = await response.json();
        
        if (data.success) {
            addLog(`✓ Hotspot started successfully`, 'success');
            addLog(`  SSID: ${config.ssid}`, 'success');
            addLog(`  hostapd PID: ${data.hostapd_pid}`, 'success');
            if (data.dnsmasq_pid) {
                addLog(`  dnsmasq PID: ${data.dnsmasq_pid}`, 'success');
            }
            addLog(`  Config file: ${data.config_file}`, 'success');
            
            setRunningState(true);
            updateCurrentConfigDisplay(config);
            startUpdates();
        } else {
            alert(`Error starting hotspot:\n${data.error}\n\n${data.details || ''}`);
            addLog(`✗ Error: ${data.error}`, 'error');
            if (data.details) {
                if (Array.isArray(data.details)) {
                    data.details.forEach(detail => addLog(`  - ${detail}`, 'error'));
                } else {
                    addLog(`  ${data.details}`, 'error');
                }
            }
            startBtn.disabled = false;
            startBtn.innerHTML = '<i data-lucide="play"></i> Start Hotspot';
            lucide.createIcons();
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        addLog(`✗ Error: ${error.message}`, 'error');
        const startBtn = document.getElementById('startBtn');
        startBtn.disabled = false;
        startBtn.innerHTML = '<i data-lucide="play"></i> Start Hotspot';
        lucide.createIcons();
    }
}

// Stop hotspot
async function stopHotspot() {
    if (!confirm('Are you sure you want to stop the hotspot?')) {
        return;
    }
    
    try {
        const stopBtn = document.getElementById('stopBtn');
        stopBtn.disabled = true;
        stopBtn.innerHTML = '<span class="loading"></span> Stopping...';
        
        addLog('Stopping hotspot...');
        
        const response = await fetch('/api/stop', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            addLog('✓ Hotspot stopped successfully', 'success');
            setRunningState(false);
            stopUpdates();
        } else {
            alert(`Error stopping hotspot: ${data.error}`);
            addLog(`✗ Error: ${data.error}`, 'error');
            stopBtn.disabled = false;
            stopBtn.innerHTML = '<i data-lucide="square"></i> Stop Hotspot';
            lucide.createIcons();
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
        addLog(`✗ Error: ${error.message}`, 'error');
        const stopBtn = document.getElementById('stopBtn');
        stopBtn.disabled = false;
        stopBtn.innerHTML = '<i data-lucide="square"></i> Stop Hotspot';
        lucide.createIcons();
    }
}

// Update current configuration display
function updateCurrentConfigDisplay(config) {
    document.getElementById('currentSsid').textContent = config.ssid || '-';
    
    // WiFi Standard
    let standard = [];
    if (config.ieee80211ax) standard.push('WiFi 6 (802.11ax)');
    if (config.ieee80211ac) standard.push('WiFi 5 (802.11ac)');
    if (config.ieee80211n) standard.push('WiFi 4 (802.11n)');
    document.getElementById('currentStandard').textContent = standard.join(', ') || 'Legacy';
    
    // Frequency
    document.getElementById('currentFreq').textContent = config.freqBand === '5' ? '5 GHz' : '2.4 GHz';
    
    // Channel
    document.getElementById('currentChannel').textContent = config.channel || '-';
    
    // Security
    let security = 'Open';
    if (config.password) {
        if (config.wpaVersion === '3') {
            security = 'WPA3 (SAE)';
        } else if (config.wpaVersion === '2') {
            security = 'WPA2';
        } else {
            security = 'WPA';
        }
    }
    document.getElementById('currentSecurity').textContent = security;
    
    document.getElementById('currentConfigPanel').style.display = 'block';
}

// Set running state
function setRunningState(running) {
    isRunning = running;
    
    const statusBadge = document.getElementById('statusBadge');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statsGrid = document.getElementById('statsGrid');
    const clientsPanel = document.getElementById('clientsPanel');
    const trafficPanel = document.getElementById('trafficPanel');
    const currentConfigPanel = document.getElementById('currentConfigPanel');
    
    const inputs = document.querySelectorAll('#configForm input, #configForm select');
    
    if (running) {
        statusBadge.className = 'status-badge status-active';
        statusBadge.innerHTML = '<span class="status-dot"></span><span>Active</span>';
        startBtn.style.display = 'none';
        stopBtn.style.display = 'block';
        stopBtn.disabled = false;
        stopBtn.innerHTML = '<i data-lucide="square"></i> Stop Hotspot';
        statsGrid.style.display = 'grid';
        clientsPanel.style.display = 'block';
        trafficPanel.style.display = 'block';
        currentConfigPanel.style.display = 'block';
        inputs.forEach(input => input.disabled = true);
        document.getElementById('loadLastConfig').disabled = true;
        document.getElementById('viewConfig').disabled = false;
    } else {
        statusBadge.className = 'status-badge status-inactive';
        statusBadge.innerHTML = '<span class="status-dot"></span><span>Inactive</span>';
        startBtn.style.display = 'block';
        startBtn.disabled = false;
        startBtn.innerHTML = '<i data-lucide="play"></i> Start Hotspot';
        stopBtn.style.display = 'none';
        statsGrid.style.display = 'none';
        clientsPanel.style.display = 'none';
        trafficPanel.style.display = 'none';
        currentConfigPanel.style.display = 'none';
        inputs.forEach(input => input.disabled = false);
        document.getElementById('loadLastConfig').disabled = false;
        document.getElementById('internetInterface').disabled = document.getElementById('noInternet').checked;
    }
    
    lucide.createIcons();
}

// Update status
async function updateStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();
        
        // Check if still running
        if (!data.status.isRunning && isRunning) {
            addLog('⚠ Hotspot stopped unexpectedly', 'warning');
            setRunningState(false);
            stopUpdates();
            return;
        }
        
        // Update uptime
        document.getElementById('uptime').textContent = formatUptime(data.status.uptime);
        
        // Update clients
        document.getElementById('clientCount').textContent = data.clientCount;
        
        const clientList = document.getElementById('clientList');
        if (data.clients.length === 0) {
            clientList.innerHTML = `
                <div class="empty-state">
                    <i data-lucide="wifi-off" style="width: 48px; height: 48px; margin: 0 auto 12px;"></i>
                    <p>No clients connected yet</p>
                </div>
            `;
            lucide.createIcons();
        } else {
            clientList.innerHTML = data.clients.map(client => {
                const hostname = client.hostname || 'Unknown Device';
                const ip = client.ip || 'Obtaining IP...';
                const mac = client.mac;
                const signal = client.signal ? `Signal: ${client.signal} dBm` : '';
                
                return `
                    <div class="client-item">
                        <div class="client-header">
                            <span class="client-name">
                                <i data-lucide="smartphone" style="width: 14px; height: 14px; display: inline-block; vertical-align: middle;"></i>
                                ${hostname}
                            </span>
                            <span class="client-ip">${ip}</span>
                        </div>
                        <div class="client-mac">${mac}</div>
                        ${signal ? `<div style="font-size: 11px; color: #a0aec0; margin-top: 4px;">${signal}</div>` : ''}
                    </div>
                `;
            }).join('');
            lucide.createIcons();
        }
        
        // Calculate rates
        const wifiTxRate = lastStats.wifi.txBytes ? 
            (data.wifiStats.txBytes - lastStats.wifi.txBytes) / 2 : 0;
        const wifiRxRate = lastStats.wifi.rxBytes ? 
            (data.wifiStats.rxBytes - lastStats.wifi.rxBytes) / 2 : 0;
        
        document.getElementById('txRate').textContent = formatBytes(wifiTxRate) + '/s';
        document.getElementById('rxRate').textContent = formatBytes(wifiRxRate) + '/s';
        
        // Update traffic stats
        document.getElementById('wifiTx').textContent = formatBytes(data.wifiStats.txBytes);
        document.getElementById('wifiRx').textContent = formatBytes(data.wifiStats.rxBytes);
        document.getElementById('ethTx').textContent = formatBytes(data.internetStats.txBytes);
        document.getElementById('ethRx').textContent = formatBytes(data.internetStats.rxBytes);
        
        const total = data.wifiStats.txBytes + data.wifiStats.rxBytes + 
                      data.internetStats.txBytes + data.internetStats.rxBytes;
        document.getElementById('totalTraffic').textContent = formatBytes(total);
        
        // Save last stats
        lastStats.wifi = data.wifiStats;
        lastStats.internet = data.internetStats;
        
        // Parse logs for client events
        if (data.status.logs && data.status.logs.length > 0) {
            data.status.logs.forEach(log => {
                const msg = log.message;
                
                // Detect client connection
                if (msg.includes('AP-STA-CONNECTED')) {
                    const macMatch = msg.match(/([0-9a-fA-F:]{17})/);
                    if (macMatch) {
                        const mac = macMatch[1];
                        // Check if we already logged this
                        const recentLogs = Array.from(document.getElementById('logsContainer').children)
                            .slice(0, 5)
                            .map(el => el.textContent);
                        if (!recentLogs.some(l => l.includes(mac) && l.includes('connected'))) {
                            addLog(`✓ Client connected: ${mac}`, 'success');
                        }
                    }
                }
                // Detect client disconnection
                else if (msg.includes('AP-STA-DISCONNECTED')) {
                    const macMatch = msg.match(/([0-9a-fA-F:]{17})/);
                    if (macMatch) {
                        const mac = macMatch[1];
                        const recentLogs = Array.from(document.getElementById('logsContainer').children)
                            .slice(0, 5)
                            .map(el => el.textContent);
                        if (!recentLogs.some(l => l.includes(mac) && l.includes('disconnected'))) {
                            addLog(`✗ Client disconnected: ${mac}`, 'warning');
                        }
                    }
                }
            });
        }
        
    } catch (error) {
        console.error('Error updating status:', error);
        addLog(`⚠ Error updating status: ${error.message}`, 'warning');
    }
}

// Start updates
function startUpdates() {
    updateStatus();
    updateInterval = setInterval(updateStatus, 2000);
}

// Stop updates
function stopUpdates() {
    if (updateInterval) {
        clearInterval(updateInterval);
        updateInterval = null;
    }
    lastStats = { wifi: {}, internet: {} };
}

// Format bytes
function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Format uptime
function formatUptime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = seconds % 60;
    return `${h}h ${m}m ${s}s`;
}

// Add log entry
function addLog(message, type = 'info') {
    const container = document.getElementById('logsContainer');
    
    // Clear "initializing" message
    if (container.children.length === 1 && container.children[0].textContent.includes('Initializing')) {
        container.innerHTML = '';
    }
    
    const timestamp = new Date().toLocaleTimeString();
    const entry = document.createElement('div');
    entry.className = `log-entry log-${type}`;
    entry.textContent = `[${timestamp}] ${message}`;
    container.insertBefore(entry, container.firstChild);
    
    // Keep only last 50 logs
    while (container.children.length > 50) {
        container.removeChild(container.lastChild);
    }
}
