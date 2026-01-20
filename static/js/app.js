// Global state
let isRunning = false;
let updateInterval = null;
let lastStats = { wifi: {}, internet: {} };

// Initialize Lucide icons
document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();
    init();
});

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

// Initialize application
async function init() {
    await loadInterfaces();
    
    // Initialize channel list for default frequency (2.4 GHz)
    updateChannelList('2.4');
    
    await checkStatus();
    await loadLastConfig();
    updateCommandPreview();
    setupEventListeners();
    addLog('WiFi Hotspot Manager initialized', 'success');
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
    
    updateCommandPreview();
}

// Setup event listeners
function setupEventListeners() {
    document.getElementById('startBtn').addEventListener('click', startHotspot);
    document.getElementById('stopBtn').addEventListener('click', stopHotspot);
    document.getElementById('loadLastConfig').addEventListener('click', loadLastConfig);
    document.getElementById('toggleAdvanced').addEventListener('click', toggleAdvancedSettings);
    document.getElementById('toggleWifiCapab').addEventListener('click', toggleWifiCapabilities);
    
    // Update command preview on any input change
    const formElements = document.querySelectorAll('#configForm input, #configForm select');
    formElements.forEach(element => {
        element.addEventListener('change', updateCommandPreview);
        element.addEventListener('input', updateCommandPreview);
    });
    
    // Show/hide daemon options
    document.getElementById('daemon').addEventListener('change', (e) => {
        document.getElementById('daemonOptions').style.display = e.target.checked ? 'block' : 'none';
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
        updateCommandPreview();
    });
}

// Toggle WiFi capabilities section
function toggleWifiCapabilities() {
    const wifiCapabSettings = document.getElementById('wifiCapabSettings');
    const toggleBtn = document.getElementById('toggleWifiCapab');
    
    if (wifiCapabSettings.style.display === 'none') {
        wifiCapabSettings.style.display = 'block';
        toggleBtn.textContent = '⚙️ Hide Advanced WiFi Capabilities';
    } else {
        wifiCapabSettings.style.display = 'none';
        toggleBtn.textContent = '⚙️ Advanced WiFi Capabilities (Optional)';
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
    if (config.method) document.getElementById('method').value = config.method;
    if (config.country) document.getElementById('country').value = config.country;
    if (config.gateway) document.getElementById('gateway').value = config.gateway;
    if (config.dhcpDns) document.getElementById('dhcpDns').value = config.dhcpDns;
    if (config.mac) document.getElementById('mac').value = config.mac;
    if (config.driver) document.getElementById('driver').value = config.driver;
    if (config.hostapdDebug) document.getElementById('hostapdDebug').value = config.hostapdDebug;
    if (config.htCapab) document.getElementById('htCapab').value = config.htCapab;
    if (config.vhtCapab) document.getElementById('vhtCapab').value = config.vhtCapab;
    if (config.macFilterAccept) document.getElementById('macFilterAccept').value = config.macFilterAccept;
    if (config.hostsFile) document.getElementById('hostsFile').value = config.hostsFile;
    if (config.pidfile) document.getElementById('pidfile').value = config.pidfile;
    if (config.logfile) document.getElementById('logfile').value = config.logfile;
    
    // Checkboxes
    document.getElementById('hidden').checked = config.hidden || false;
    document.getElementById('isolate').checked = config.isolate || false;
    document.getElementById('noVirt').checked = config.noVirt || false;
    document.getElementById('ieee80211n').checked = config.ieee80211n || false;
    document.getElementById('ieee80211ac').checked = config.ieee80211ac || false;
    document.getElementById('macFilter').checked = config.macFilter || false;
    document.getElementById('redirectToLocalhost').checked = config.redirectToLocalhost || false;
    document.getElementById('noInternet').checked = config.noInternet || false;
    document.getElementById('noDns').checked = config.noDns || false;
    document.getElementById('noDnsmasq').checked = config.noDnsmasq || false;
    document.getElementById('dnsHosts').checked = config.dnsHosts || false;
    document.getElementById('noHaveged').checked = config.noHaveged || false;
    document.getElementById('fixUnmanaged').checked = config.fixUnmanaged || false;
    document.getElementById('psk').checked = config.psk || false;
    document.getElementById('daemon').checked = config.daemon || false;
    
    // Show daemon options if daemon is checked
    if (config.daemon) {
        document.getElementById('daemonOptions').style.display = 'block';
    }
    
    updateCommandPreview();
}

// Get configuration from form
function getConfig() {
    const config = {
        wifiInterface: document.getElementById('wifiInterface').value,
        ssid: document.getElementById('ssid').value,
        password: document.getElementById('password').value,
        wpaVersion: document.getElementById('wpaVersion').value,
        channel: document.getElementById('channel').value,
        
        // Advanced settings
        method: document.getElementById('method').value,
        freqBand: document.getElementById('freqBand').value,
        country: document.getElementById('country').value.toUpperCase(),
        gateway: document.getElementById('gateway').value,
        dhcpDns: document.getElementById('dhcpDns').value,
        mac: document.getElementById('mac').value,
        driver: document.getElementById('driver').value,
        hostapdDebug: document.getElementById('hostapdDebug').value,
        htCapab: document.getElementById('htCapab').value,
        vhtCapab: document.getElementById('vhtCapab').value,
        macFilterAccept: document.getElementById('macFilterAccept').value,
        hostsFile: document.getElementById('hostsFile').value,
        pidfile: document.getElementById('pidfile').value,
        logfile: document.getElementById('logfile').value,
        
        // Checkboxes
        hidden: document.getElementById('hidden').checked,
        isolate: document.getElementById('isolate').checked,
        noVirt: document.getElementById('noVirt').checked,
        ieee80211n: document.getElementById('ieee80211n').checked,
        ieee80211ac: document.getElementById('ieee80211ac').checked,
        macFilter: document.getElementById('macFilter').checked,
        redirectToLocalhost: document.getElementById('redirectToLocalhost').checked,
        noInternet: document.getElementById('noInternet').checked,
        noDns: document.getElementById('noDns').checked,
        noDnsmasq: document.getElementById('noDnsmasq').checked,
        dnsHosts: document.getElementById('dnsHosts').checked,
        noHaveged: document.getElementById('noHaveged').checked,
        fixUnmanaged: document.getElementById('fixUnmanaged').checked,
        psk: document.getElementById('psk').checked,
        daemon: document.getElementById('daemon').checked
    };
    
    // Only add internetInterface if not disabled
    if (!config.noInternet) {
        config.internetInterface = document.getElementById('internetInterface').value;
    }
    
    return config;
}

// Update command preview
function updateCommandPreview() {
    const config = getConfig();
    let cmd = 'sudo create_ap';
    
    // Add all options
    if (config.channel) cmd += ` -c ${config.channel}`;
    if (config.wpaVersion) cmd += ` -w ${config.wpaVersion}`;
    if (config.noInternet) cmd += ' -n';
    if (config.method && config.method !== 'nat') cmd += ` -m ${config.method}`;
    if (config.psk) cmd += ' --psk';
    if (config.hidden) cmd += ' --hidden';
    if (config.macFilter) cmd += ' --mac-filter';
    if (config.macFilterAccept) cmd += ` --mac-filter-accept ${config.macFilterAccept}`;
    if (config.redirectToLocalhost) cmd += ' --redirect-to-localhost';
    if (config.hostapdDebug) cmd += ` --hostapd-debug ${config.hostapdDebug}`;
    if (config.isolate) cmd += ' --isolate-clients';
    
    // IEEE 802.11n/ac
    if (config.ieee80211n) {
        cmd += ' --ieee80211n';
        if (config.htCapab) {
            cmd += ` --ht_capab "${config.htCapab}"`;
        }
    }
    if (config.ieee80211ac) {
        cmd += ' --ieee80211ac';
        if (config.vhtCapab) {
            cmd += ` --vht_capab "${config.vhtCapab}"`;
        }
    }
    
    if (config.country) cmd += ` --country ${config.country}`;
    if (config.freqBand) cmd += ` --freq-band ${config.freqBand}`;
    if (config.driver) cmd += ` --driver ${config.driver}`;
    if (config.noVirt) cmd += ' --no-virt';
    if (config.noHaveged) cmd += ' --no-haveged';
    if (config.fixUnmanaged) cmd += ' --fix-unmanaged';
    if (config.mac) cmd += ` --mac ${config.mac}`;
    if (config.dhcpDns) cmd += ` --dhcp-dns ${config.dhcpDns}`;
    if (config.daemon) cmd += ' --daemon';
    if (config.pidfile) cmd += ` --pidfile ${config.pidfile}`;
    if (config.logfile) cmd += ` --logfile ${config.logfile}`;
    if (config.gateway) cmd += ` -g ${config.gateway}`;
    if (config.noDns) cmd += ' --no-dns';
    if (config.noDnsmasq) cmd += ' --no-dnsmasq';
    if (config.dnsHosts) cmd += ' -d';
    if (config.hostsFile) cmd += ` -e ${config.hostsFile}`;
    
    // Required parameters
    cmd += ` ${config.wifiInterface}`;
    if (config.internetInterface && !config.noInternet) {
        cmd += ` ${config.internetInterface}`;
    }
    cmd += ` "${config.ssid}"`;
    if (config.password) {
        cmd += ` "${config.password}"`;
    }
    
    document.getElementById('commandPreview').textContent = cmd;
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
            addLog(`  PID: ${data.pid}`, 'success');
            addLog(`  Mode: ${data.mode}`, 'success');
            setRunningState(true);
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

// Set running state
function setRunningState(running) {
    isRunning = running;
    
    const statusBadge = document.getElementById('statusBadge');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const statsGrid = document.getElementById('statsGrid');
    const clientsPanel = document.getElementById('clientsPanel');
    const trafficPanel = document.getElementById('trafficPanel');
    
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
        inputs.forEach(input => input.disabled = true);
        document.getElementById('loadLastConfig').disabled = true;
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
        
        // Update logs if available
        if (data.status.logs && data.status.logs.length > 0) {
            const logsContainer = document.getElementById('logsContainer');
            
            // Parse logs for client events
            data.status.logs.forEach(log => {
                const msg = log.message;
                
                // Detect client connection
                if (msg.includes('AP-STA-CONNECTED')) {
                    const macMatch = msg.match(/([0-9a-fA-F:]{17})/);
                    if (macMatch) {
                        const mac = macMatch[1];
                        addLog(`✓ Client connected: ${mac}`, 'success');
                    }
                }
                // Detect client disconnection
                else if (msg.includes('AP-STA-DISCONNECTED')) {
                    const macMatch = msg.match(/([0-9a-fA-F:]{17})/);
                    if (macMatch) {
                        const mac = macMatch[1];
                        addLog(`✗ Client disconnected: ${mac}`, 'warning');
                    }
                }
                // Detect authentication
                else if (msg.includes('4WAY-HS-COMPLETED') || msg.includes('WPA: pairwise key handshake completed')) {
                    const macMatch = msg.match(/([0-9a-fA-F:]{17})/);
                    if (macMatch) {
                        const mac = macMatch[1];
                        addLog(`🔐 Client authenticated: ${mac}`, 'success');
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
    if (container.children.length === 1 && container.children[0].textContent === 'Initializing...') {
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
