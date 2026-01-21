#!/usr/bin/env python3
"""
WiFi Hotspot Manager for Orange Pi
Uses hostapd + dnsmasq for full control
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import re
import os
import signal
import psutil
import json
import tempfile
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Configuration paths
STATE_FILE = '/var/run/hostapd_manager.json'
CONFIG_DIR = '/etc/hostapd_manager'
HOSTAPD_CONF = f'{CONFIG_DIR}/hostapd.conf'
DNSMASQ_CONF = f'{CONFIG_DIR}/dnsmasq.conf'
LAST_CONFIG_FILE = f'{CONFIG_DIR}/last_config.json'

class HotspotManager:
    def __init__(self):
        self.hostapd_process = None
        self.dnsmasq_process = None
        self.is_running = False
        self.start_time = None
        self.config = {}
        self.lock = threading.Lock()
        self.log_buffer = []
        
        # Ensure config directory exists
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Try to restore state on startup
        self.restore_state()
        
    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                'is_running': self.is_running,
                'start_time': self.start_time,
                'config': self.config,
                'hostapd_pid': self.hostapd_process.pid if self.hostapd_process else None,
                'dnsmasq_pid': self.dnsmasq_process.pid if self.dnsmasq_process else None,
                'timestamp': time.time()
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Also save config separately
            if self.config:
                with open(LAST_CONFIG_FILE, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def restore_state(self):
        """Restore state from file"""
        try:
            if not os.path.exists(STATE_FILE):
                return
            
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            
            # Check if processes are still running
            hostapd_pid = state.get('hostapd_pid')
            dnsmasq_pid = state.get('dnsmasq_pid')
            
            if hostapd_pid and self.is_process_running(hostapd_pid, 'hostapd'):
                self.is_running = True
                self.start_time = state.get('start_time')
                self.config = state.get('config', {})
                
                try:
                    self.hostapd_process = psutil.Process(hostapd_pid)
                    if dnsmasq_pid:
                        self.dnsmasq_process = psutil.Process(dnsmasq_pid)
                    print(f"✅ Restored connection to running hotspot (PID: {hostapd_pid})")
                except:
                    pass
            else:
                self.clear_state()
                print("ℹ️ No active hotspot found")
                
        except Exception as e:
            print(f"Error restoring state: {e}")
            self.clear_state()
    
    def clear_state(self):
        """Clear state file"""
        try:
            if os.path.exists(STATE_FILE):
                os.remove(STATE_FILE)
        except:
            pass
    
    def is_process_running(self, pid, name):
        """Check if a process is running"""
        try:
            process = psutil.Process(pid)
            return name in ' '.join(process.cmdline())
        except:
            return False
        
    def check_prerequisites(self):
        """Check if hostapd and dnsmasq are installed"""
        errors = []
        
        # Check root access
        if os.geteuid() != 0:
            errors.append("Must run as root (use sudo)")
        
        # Check hostapd
        try:
            result = subprocess.run(['which', 'hostapd'], capture_output=True, timeout=2)
            if result.returncode != 0:
                errors.append("hostapd is not installed. Install with: sudo apt install hostapd")
        except:
            errors.append("Cannot check hostapd")
        
        # Check dnsmasq
        try:
            result = subprocess.run(['which', 'dnsmasq'], capture_output=True, timeout=2)
            if result.returncode != 0:
                errors.append("dnsmasq is not installed. Install with: sudo apt install dnsmasq")
        except:
            errors.append("Cannot check dnsmasq")
        
        return errors
    
    def generate_hostapd_conf(self, config):
        """Generate hostapd.conf file"""
        conf_lines = []
        
        # Basic interface settings
        conf_lines.append(f"interface={config.get('wifiInterface', 'wlan0')}")
        conf_lines.append(f"driver={config.get('driver', 'nl80211')}")
        conf_lines.append(f"ssid={config.get('ssid', 'OrangePi-Hotspot')}")
        
        # Hardware mode based on frequency band
        freq_band = config.get('freqBand', '2.4')
        if freq_band == '5':
            conf_lines.append("hw_mode=a")
        else:
            conf_lines.append("hw_mode=g")
        
        # Channel
        channel = config.get('channel', '6' if freq_band == '2.4' else '36')
        conf_lines.append(f"channel={channel}")
        
        # Country code
        if config.get('country'):
            conf_lines.append(f"country_code={config['country'].upper()}")
        
        # IEEE 802.11n
        if config.get('ieee80211n'):
            conf_lines.append("ieee80211n=1")
            
            # HT capabilities
            if config.get('htCapab'):
                conf_lines.append(f"ht_capab={config['htCapab']}")
            else:
                # Default HT capabilities
                conf_lines.append("ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40][DSSS_CCK-40]")
        
        # IEEE 802.11ac
        if config.get('ieee80211ac'):
            conf_lines.append("ieee80211ac=1")
            
            # VHT operation
            conf_lines.append("vht_oper_chwidth=1")
            
            # Calculate center frequency
            try:
                ch = int(channel)
                if ch >= 36 and ch <= 48:
                    center_freq = 42
                elif ch >= 52 and ch <= 64:
                    center_freq = 58
                elif ch >= 100 and ch <= 112:
                    center_freq = 106
                elif ch >= 116 and ch <= 128:
                    center_freq = 122
                elif ch >= 132 and ch <= 144:
                    center_freq = 138
                elif ch >= 149 and ch <= 161:
                    center_freq = 155
                else:
                    center_freq = ch + 6
                
                conf_lines.append(f"vht_oper_centr_freq_seg0_idx={center_freq}")
            except:
                conf_lines.append("vht_oper_centr_freq_seg0_idx=42")
            
            # VHT capabilities
            if config.get('vhtCapab'):
                conf_lines.append(f"vht_capab={config['vhtCapab']}")
        
        # IEEE 802.11ax (WiFi 6)
        if config.get('ieee80211ax'):
            conf_lines.append("ieee80211ax=1")
            if config.get('heCapab'):
                conf_lines.append(f"he_capab={config['heCapab']}")
        
        # Security settings
        password = config.get('password', '')
        if password:
            wpa_version = config.get('wpaVersion', '2')
            
            if wpa_version == '3':
                # WPA3
                conf_lines.append("wpa=2")
                conf_lines.append("wpa_key_mgmt=SAE")
                conf_lines.append("rsn_pairwise=CCMP")
                conf_lines.append(f"sae_password={password}")
            else:
                # WPA/WPA2
                conf_lines.append(f"wpa={wpa_version}")
                conf_lines.append("wpa_key_mgmt=WPA-PSK")
                
                if config.get('psk'):
                    conf_lines.append(f"wpa_psk={password}")
                else:
                    conf_lines.append(f"wpa_passphrase={password}")
                
                conf_lines.append("rsn_pairwise=CCMP")
        
        # Authentication algorithm
        conf_lines.append("auth_algs=1")
        
        # WMM (WiFi Multimedia)
        conf_lines.append("wmm_enabled=1")
        
        # Hidden SSID
        if config.get('hidden'):
            conf_lines.append("ignore_broadcast_ssid=1")
        
        # Client isolation
        if config.get('isolate'):
            conf_lines.append("ap_isolate=1")
        
        # MAC filtering
        if config.get('macFilter'):
            conf_lines.append("macaddr_acl=1")
            if config.get('macFilterAccept'):
                conf_lines.append(f"accept_mac_file={config['macFilterAccept']}")
        
        # Additional hostapd options
        if config.get('hostapdDebug'):
            conf_lines.append(f"logger_syslog_level={config['hostapdDebug']}")
        
        # Max number of stations
        if config.get('maxStations'):
            conf_lines.append(f"max_num_sta={config['maxStations']}")
        
        return '\n'.join(conf_lines) + '\n'
    
    def generate_dnsmasq_conf(self, config):
        """Generate dnsmasq.conf file"""
        conf_lines = []
        
        interface = config.get('wifiInterface', 'wlan0')
        gateway = config.get('gateway', '192.168.12.1')
        
        # Interface
        conf_lines.append(f"interface={interface}")
        conf_lines.append("bind-interfaces")
        
        # DHCP range
        dhcp_start = config.get('dhcpStart', '192.168.12.10')
        dhcp_end = config.get('dhcpEnd', '192.168.12.100')
        lease_time = config.get('leaseTime', '12h')
        
        conf_lines.append(f"dhcp-range={dhcp_start},{dhcp_end},{lease_time}")
        
        # Gateway
        conf_lines.append(f"dhcp-option=3,{gateway}")
        
        # DNS servers
        dns_servers = config.get('dhcpDns', '8.8.8.8,8.8.4.4')
        for dns in dns_servers.split(','):
            conf_lines.append(f"dhcp-option=6,{dns.strip()}")
        
        # Domain
        if config.get('domain'):
            conf_lines.append(f"domain={config['domain']}")
        
        # Additional hosts file
        if config.get('hostsFile') and os.path.exists(config['hostsFile']):
            conf_lines.append(f"addn-hosts={config['hostsFile']}")
        
        # No DNS
        if config.get('noDns'):
            conf_lines.append("port=0")
        
        return '\n'.join(conf_lines) + '\n'
    
    def setup_interface(self, config):
        """Setup network interface"""
        interface = config.get('wifiInterface', 'wlan0')
        gateway = config.get('gateway', '192.168.12.1')
        
        try:
            # Bring interface down
            subprocess.run(['ip', 'link', 'set', interface, 'down'], check=True)
            
            # Set IP address
            subprocess.run(['ip', 'addr', 'flush', 'dev', interface], check=True)
            subprocess.run(['ip', 'addr', 'add', f'{gateway}/24', 'dev', interface], check=True)
            
            # Bring interface up
            subprocess.run(['ip', 'link', 'set', interface, 'up'], check=True)
            
            return True
        except Exception as e:
            print(f"Error setting up interface: {e}")
            return False
    
    def setup_nat(self, config):
        """Setup NAT and IP forwarding"""
        if config.get('noInternet'):
            return True
        
        try:
            wifi_iface = config.get('wifiInterface', 'wlan0')
            inet_iface = config.get('internetInterface', 'eth0')
            
            # Enable IP forwarding
            with open('/proc/sys/net/ipv4/ip_forward', 'w') as f:
                f.write('1\n')
            
            # Setup iptables NAT
            subprocess.run(['iptables', '-t', 'nat', '-A', 'POSTROUTING', 
                          '-o', inet_iface, '-j', 'MASQUERADE'], check=True)
            subprocess.run(['iptables', '-A', 'FORWARD', '-i', inet_iface, 
                          '-o', wifi_iface, '-m', 'state', '--state', 
                          'RELATED,ESTABLISHED', '-j', 'ACCEPT'], check=True)
            subprocess.run(['iptables', '-A', 'FORWARD', '-i', wifi_iface, 
                          '-o', inet_iface, '-j', 'ACCEPT'], check=True)
            
            return True
        except Exception as e:
            print(f"Error setting up NAT: {e}")
            return False
    
    def cleanup_nat(self, config):
        """Cleanup NAT rules"""
        try:
            wifi_iface = config.get('wifiInterface', 'wlan0')
            inet_iface = config.get('internetInterface', 'eth0')
            
            # Remove iptables rules
            subprocess.run(['iptables', '-t', 'nat', '-D', 'POSTROUTING', 
                          '-o', inet_iface, '-j', 'MASQUERADE'], 
                         stderr=subprocess.DEVNULL)
            subprocess.run(['iptables', '-D', 'FORWARD', '-i', inet_iface, 
                          '-o', wifi_iface, '-m', 'state', '--state', 
                          'RELATED,ESTABLISHED', '-j', 'ACCEPT'],
                         stderr=subprocess.DEVNULL)
            subprocess.run(['iptables', '-D', 'FORWARD', '-i', wifi_iface, 
                          '-o', inet_iface, '-j', 'ACCEPT'],
                         stderr=subprocess.DEVNULL)
        except:
            pass
    
    def start(self, config):
        """Start the WiFi hotspot"""
        with self.lock:
            if self.is_running:
                return {'success': False, 'error': 'Hotspot is already running'}
            
            # Check prerequisites
            prereq_errors = self.check_prerequisites()
            if prereq_errors:
                return {
                    'success': False,
                    'error': 'Prerequisites check failed',
                    'details': prereq_errors
                }
            
            try:
                # Generate configuration files
                hostapd_conf = self.generate_hostapd_conf(config)
                dnsmasq_conf = self.generate_dnsmasq_conf(config)
                
                # Write configuration files
                with open(HOSTAPD_CONF, 'w') as f:
                    f.write(hostapd_conf)
                
                with open(DNSMASQ_CONF, 'w') as f:
                    f.write(dnsmasq_conf)
                
                # Setup network interface
                if not self.setup_interface(config):
                    return {'success': False, 'error': 'Failed to setup network interface'}
                
                # Start dnsmasq
                if not config.get('noDnsmasq'):
                    self.dnsmasq_process = subprocess.Popen(
                        ['dnsmasq', '-C', DNSMASQ_CONF, '-d'],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    time.sleep(1)
                    
                    if self.dnsmasq_process.poll() is not None:
                        return {'success': False, 'error': 'Failed to start dnsmasq'}
                
                # Setup NAT
                if not self.setup_nat(config):
                    if self.dnsmasq_process:
                        self.dnsmasq_process.terminate()
                    return {'success': False, 'error': 'Failed to setup NAT'}
                
                # Start hostapd
                self.hostapd_process = subprocess.Popen(
                    ['hostapd', HOSTAPD_CONF],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Wait and check if hostapd started successfully
                time.sleep(2)
                if self.hostapd_process.poll() is not None:
                    stdout, stderr = self.hostapd_process.communicate()
                    self.cleanup_nat(config)
                    if self.dnsmasq_process:
                        self.dnsmasq_process.terminate()
                    return {
                        'success': False,
                        'error': 'hostapd failed to start',
                        'details': stderr or stdout
                    }
                
                self.is_running = True
                self.start_time = time.time()
                self.config = config
                self.save_state()
                
                # Start log monitoring
                threading.Thread(target=self.monitor_hostapd_logs, daemon=True).start()
                
                return {
                    'success': True,
                    'hostapd_pid': self.hostapd_process.pid,
                    'dnsmasq_pid': self.dnsmasq_process.pid if self.dnsmasq_process else None,
                    'config_file': HOSTAPD_CONF
                }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop the WiFi hotspot"""
        with self.lock:
            if not self.is_running:
                return {'success': False, 'error': 'Hotspot is not running'}
            
            try:
                # Stop hostapd
                if self.hostapd_process:
                    self.hostapd_process.terminate()
                    try:
                        self.hostapd_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.hostapd_process.kill()
                    self.hostapd_process = None
                
                # Stop dnsmasq
                if self.dnsmasq_process:
                    self.dnsmasq_process.terminate()
                    try:
                        self.dnsmasq_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.dnsmasq_process.kill()
                    self.dnsmasq_process = None
                
                # Cleanup NAT
                self.cleanup_nat(self.config)
                
                # Flush interface
                interface = self.config.get('wifiInterface', 'wlan0')
                try:
                    subprocess.run(['ip', 'addr', 'flush', 'dev', interface])
                    subprocess.run(['ip', 'link', 'set', interface, 'down'])
                except:
                    pass
                
                self.is_running = False
                self.start_time = None
                self.log_buffer = []
                self.clear_state()
                
                return {'success': True}
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def monitor_hostapd_logs(self):
        """Monitor hostapd output"""
        if not self.hostapd_process:
            return
        
        try:
            for line in self.hostapd_process.stdout:
                self.log_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line.strip()
                })
                if len(self.log_buffer) > 100:
                    self.log_buffer.pop(0)
        except:
            pass
    
    def get_status(self):
        """Get current hotspot status"""
        uptime = 0
        if self.is_running and self.start_time:
            uptime = int(time.time() - self.start_time)
        
        # Check if processes are still alive
        if self.is_running:
            if self.hostapd_process and self.hostapd_process.poll() is not None:
                self.is_running = False
                self.start_time = None
                self.clear_state()
        
        return {
            'isRunning': self.is_running,
            'uptime': uptime,
            'config': self.config,
            'logs': self.log_buffer[-20:] if self.log_buffer else [],
            'hostapd_pid': self.hostapd_process.pid if self.hostapd_process else None,
            'dnsmasq_pid': self.dnsmasq_process.pid if self.dnsmasq_process else None
        }
    
    def get_connected_clients(self):
        """Get list of connected clients"""
        clients_dict = {}
        
        if not self.is_running:
            return []
        
        try:
            interface = self.config.get('wifiInterface', 'wlan0')
            
            # Method 1: Parse hostapd logs
            for log in self.log_buffer:
                msg = log.get('message', '')
                if 'AP-STA-CONNECTED' in msg:
                    match = re.search(r'([0-9a-fA-F:]{17})', msg)
                    if match:
                        mac = match.group(1).lower()
                        clients_dict[mac] = {'mac': mac, 'ip': None, 'hostname': None}
                elif 'AP-STA-DISCONNECTED' in msg:
                    match = re.search(r'([0-9a-fA-F:]{17})', msg)
                    if match:
                        mac = match.group(1).lower()
                        if mac in clients_dict:
                            del clients_dict[mac]
            
            # Method 2: Use iw station dump
            result = subprocess.run(
                ['iw', 'dev', interface, 'station', 'dump'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                current_mac = None
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line.startswith('Station'):
                        mac = line.split()[1].lower()
                        current_mac = mac
                        if mac not in clients_dict:
                            clients_dict[mac] = {'mac': mac, 'ip': None, 'hostname': None, 'signal': None}
                    elif 'signal:' in line and current_mac:
                        signal_strength = line.split(':')[1].strip().split()[0]
                        clients_dict[current_mac]['signal'] = signal_strength
            
            # Method 3: Get IP from DHCP leases
            lease_file = '/var/lib/misc/dnsmasq.leases'
            if os.path.exists(lease_file):
                with open(lease_file, 'r') as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            mac = parts[1].lower()
                            ip = parts[2]
                            hostname = parts[3] if len(parts) > 3 else None
                            
                            if mac in clients_dict:
                                clients_dict[mac]['ip'] = ip
                                clients_dict[mac]['hostname'] = hostname or f"Device-{ip.split('.')[-1]}"
        
        except Exception as e:
            print(f"Error getting clients: {e}")
        
        return list(clients_dict.values())
    
    def get_interface_stats(self, interface):
        """Get network interface statistics"""
        try:
            stats = psutil.net_io_counters(pernic=True)
            if interface in stats:
                return {
                    'txBytes': stats[interface].bytes_sent,
                    'rxBytes': stats[interface].bytes_recv,
                    'txPackets': stats[interface].packets_sent,
                    'rxPackets': stats[interface].packets_recv
                }
        except:
            pass
        
        return {'txBytes': 0, 'rxBytes': 0, 'txPackets': 0, 'rxPackets': 0}
    
    def get_last_config(self):
        """Get last saved configuration"""
        try:
            if os.path.exists(LAST_CONFIG_FILE):
                with open(LAST_CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return None

# Global manager instance
manager = HotspotManager()

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_hotspot():
    config = request.json
    result = manager.start(config)
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
def stop_hotspot():
    result = manager.stop()
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    status = manager.get_status()
    clients = manager.get_connected_clients()
    
    wifi_interface = status['config'].get('wifiInterface', 'wlan0') if status['config'] else 'wlan0'
    internet_interface = status['config'].get('internetInterface', 'eth0') if status['config'] else 'eth0'
    
    wifi_stats = manager.get_interface_stats(wifi_interface)
    internet_stats = manager.get_interface_stats(internet_interface)
    
    return jsonify({
        'status': status,
        'clients': clients,
        'clientCount': len(clients),
        'wifiStats': wifi_stats,
        'internetStats': internet_stats
    })

@app.route('/api/interfaces', methods=['GET'])
def get_interfaces():
    try:
        interfaces = []
        net_if = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for iface_name in net_if.keys():
            if iface_name == 'lo':
                continue
            
            if iface_name not in net_stats or not net_stats[iface_name].isup:
                continue
            
            iface_info = {
                'name': iface_name,
                'type': 'unknown',
                'isWireless': False,
                'supportsAP': False
            }
            
            if os.path.exists(f'/sys/class/net/{iface_name}/wireless'):
                iface_info['type'] = 'wifi'
                iface_info['isWireless'] = True
                iface_info['supportsAP'] = True
            elif 'eth' in iface_name or 'enp' in iface_name:
                iface_info['type'] = 'ethernet'
            
            interfaces.append(iface_info)
        
        return jsonify({
            'interfaces': interfaces,
            'hasWireless': any(i['isWireless'] for i in interfaces),
            'hasAPSupport': any(i['supportsAP'] for i in interfaces)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/last-config', methods=['GET'])
def get_last_config():
    config = manager.get_last_config()
    return jsonify({'config': config})

@app.route('/api/check-prerequisites', methods=['GET'])
def check_prerequisites():
    errors = manager.check_prerequisites()
    return jsonify({
        'success': len(errors) == 0,
        'errors': errors
    })

@app.route('/api/hostapd-config', methods=['GET'])
def get_hostapd_config():
    """Get current hostapd configuration"""
    try:
        if os.path.exists(HOSTAPD_CONF):
            with open(HOSTAPD_CONF, 'r') as f:
                return jsonify({'config': f.read()})
    except:
        pass
    return jsonify({'config': None})

if __name__ == '__main__':
    if os.geteuid() != 0:
        print("=" * 60)
        print("ERROR: This application MUST be run as root!")
        print("=" * 60)
        print("\nPlease run with: sudo python3 app.py")
        print("=" * 60)
        exit(1)
    
    errors = manager.check_prerequisites()
    if errors:
        print("=" * 60)
        print("PREREQUISITE CHECK FAILED:")
        print("=" * 60)
        for error in errors:
            print(f"  ❌ {error}")
        print("=" * 60)
        exit(1)
    
    print("=" * 60)
    print("✅ All prerequisites satisfied")
    
    if manager.is_running:
        print(f"✅ Restored connection to running hotspot")
        print(f"   SSID: {manager.config.get('ssid', 'Unknown')}")
    else:
        print("ℹ️  No active hotspot found")
    
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=False)
