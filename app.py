#!/usr/bin/env python3
"""
WiFi Hotspot Manager for Orange Pi
Manages create_ap commands and monitors hotspot status
Full support for all create_ap options
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
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Configuration file paths
STATE_FILE = '/var/run/create_ap_manager.json'
CONFIG_DIR = '/etc/create_ap_manager'
CONFIG_FILE = f'{CONFIG_DIR}/last_config.json'

class HotspotManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.start_time = None
        self.config = {}
        self.lock = threading.Lock()
        self.log_buffer = []
        self.pid_file = None
        
        # Ensure config directory exists
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # Try to restore state on startup
        self.restore_state()
        
    def parse_hostapd_logs(self):
        """Parse hostapd logs to get connected clients"""
        clients = {}
        
        # Try to read from log file if daemon mode
        if self.config.get('daemon') and self.config.get('logfile'):
            try:
                with open(self.config['logfile'], 'r') as f:
                    lines = f.readlines()[-100:]  # Last 100 lines
                    
                    for line in lines:
                        # Look for STA connected events
                        if 'AP-STA-CONNECTED' in line:
                            match = re.search(r'AP-STA-CONNECTED ([0-9a-fA-F:]{17})', line)
                            if match:
                                mac = match.group(1).lower()
                                clients[mac] = {'mac': mac, 'ip': None, 'hostname': None}
                        
                        # Look for STA disconnected events
                        elif 'AP-STA-DISCONNECTED' in line:
                            match = re.search(r'AP-STA-DISCONNECTED ([0-9a-fA-F:]{17})', line)
                            if match:
                                mac = match.group(1).lower()
                                if mac in clients:
                                    del clients[mac]
            except Exception as e:
                print(f"Error reading log file: {e}")
        
        # Also check from memory logs
        for log in self.log_buffer:
            msg = log.get('message', '')
            if 'AP-STA-CONNECTED' in msg:
                match = re.search(r'AP-STA-CONNECTED ([0-9a-fA-F:]{17})', msg)
                if match:
                    mac = match.group(1).lower()
                    clients[mac] = {'mac': mac, 'ip': None, 'hostname': None}
            elif 'AP-STA-DISCONNECTED' in msg:
                match = re.search(r'AP-STA-DISCONNECTED ([0-9a-fA-F:]{17})', msg)
                if match:
                    mac = match.group(1).lower()
                    if mac in clients:
                        del clients[mac]
        
        return list(clients.values())

    def get_connected_clients(self):
        """Get list of connected clients from multiple sources"""
        clients_dict = {}
        
        if not self.is_running:
            return []
        
        try:
            # Method 1: Parse logs (most reliable for daemon mode)
            log_clients = self.parse_hostapd_logs()
            for client in log_clients:
                clients_dict[client['mac']] = client
            
            # Method 2: Use create_ap --list-clients if in daemon mode
            if self.config.get('daemon'):
                wifi_iface = self.config.get('wifiInterface', 'wlan0')
                
                # Try with the actual AP interface (might be ap0)
                ap_interfaces = [wifi_iface, 'ap0', f'{wifi_iface}_0']
                
                for ap_iface in ap_interfaces:
                    try:
                        result = subprocess.run(
                            ['create_ap', '--list-clients', ap_iface],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        
                        if result.returncode == 0 and result.stdout.strip():
                            lines = result.stdout.strip().split('\n')
                            for line in lines:
                                if not line.strip() or 'No' in line:
                                    continue
                                # Parse MAC address
                                match = re.search(r'([0-9a-fA-F:]{17})', line)
                                if match:
                                    mac = match.group(1).lower()
                                    if mac not in clients_dict:
                                        clients_dict[mac] = {'mac': mac, 'ip': None, 'hostname': None}
                            break  # Found clients, stop trying other interfaces
                    except:
                        continue
            
            # Method 3: Use iw station dump
            ap_interface = self.config.get('wifiInterface', 'wlan0')
            
            # Try multiple possible AP interface names
            possible_interfaces = [ap_interface, 'ap0', f'{ap_interface}_0']
            
            for iface in possible_interfaces:
                try:
                    result = subprocess.run(
                        ['iw', 'dev', iface, 'station', 'dump'],
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
                        
                        if clients_dict:
                            break  # Found clients, stop trying other interfaces
                except:
                    continue
            
            # Method 4: Get IP addresses from ARP and DHCP leases
            for mac in list(clients_dict.keys()):
                ip = self.get_client_ip(mac)
                if ip:
                    clients_dict[mac]['ip'] = ip
                    clients_dict[mac]['hostname'] = self.get_hostname(ip)
            
            # Method 5: Check hostapd_cli if available
            try:
                result = subprocess.run(
                    ['hostapd_cli', '-i', ap_interface, 'all_sta'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    current_mac = None
                    for line in result.stdout.split('\n'):
                        if re.match(r'^[0-9a-fA-F:]{17}$', line.strip()):
                            mac = line.strip().lower()
                            current_mac = mac
                            if mac not in clients_dict:
                                clients_dict[mac] = {'mac': mac, 'ip': None, 'hostname': None}
            except:
                pass
        
        except Exception as e:
            print(f"Error getting clients: {e}")
        
        return list(clients_dict.values())        
        
    def save_state(self):
        """Save current state to file"""
        try:
            state = {
                'is_running': self.is_running,
                'start_time': self.start_time,
                'config': self.config,
                'pid': self.process.pid if self.process else None,
                'timestamp': time.time()
            }
            
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
            
            # Also save config separately for easy access
            if self.config:
                with open(CONFIG_FILE, 'w') as f:
                    json.dump(self.config, f, indent=2)
                    
        except Exception as e:
            print(f"Error saving state: {e}")
    
    def restore_state(self):
        """Restore state from file and check if process is still running"""
        try:
            # Check if state file exists
            if not os.path.exists(STATE_FILE):
                return
            
            with open(STATE_FILE, 'r') as f:
                state = json.load(f)
            
            # Check if the saved process is still running
            pid = state.get('pid')
            if pid and self.is_process_running(pid):
                # Process is still running, restore state
                self.is_running = True
                self.start_time = state.get('start_time')
                self.config = state.get('config', {})
                
                # Try to attach to the process
                try:
                    self.process = psutil.Process(pid)
                    print(f"✅ Restored connection to running hotspot (PID: {pid})")
                except:
                    # Can't attach, but we know it's running
                    print(f"⚠️ Hotspot is running (PID: {pid}) but can't attach to process")
            else:
                # Process is not running, clear state
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
    
    def is_process_running(self, pid):
        """Check if a process with given PID is running and is create_ap"""
        try:
            process = psutil.Process(pid)
            cmdline = ' '.join(process.cmdline())
            return 'create_ap' in cmdline
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def find_running_instances(self):
        """Find all running create_ap instances"""
        instances = []
        try:
            result = subprocess.run(
                ['create_ap', '--list-running'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('No'):
                        # Parse PID and interface
                        match = re.search(r'PID:\s*(\d+).*interface:\s*(\S+)', line)
                        if match:
                            instances.append({
                                'pid': int(match.group(1)),
                                'interface': match.group(2)
                            })
        except Exception as e:
            print(f"Error finding running instances: {e}")
        
        return instances
        
    def check_prerequisites(self):
        """Check if create_ap is installed and we have root access"""
        errors = []
        
        # Check root access
        if os.geteuid() != 0:
            errors.append("Must run as root (use sudo)")
        
        # Check if create_ap exists
        try:
            result = subprocess.run(
                ['which', 'create_ap'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode != 0:
                errors.append("create_ap is not installed. Install with: sudo apt install create-ap")
        except Exception as e:
            errors.append(f"Cannot check create_ap: {str(e)}")
        
        return errors
        
    def build_command(self, config):
        """Build create_ap command from configuration with ALL options"""
        cmd = ['create_ap']
        
        # Channel
        if config.get('channel'):
            cmd.extend(['-c', str(config['channel'])])
        
        # WPA Version
        if config.get('wpaVersion'):
            cmd.extend(['-w', str(config['wpaVersion'])])
        
        # Disable Internet sharing
        if config.get('noInternet'):
            cmd.append('-n')
        
        # Internet sharing method
        if config.get('method') and not config.get('noInternet'):
            cmd.extend(['-m', config['method']])
        
        # PSK mode
        if config.get('psk'):
            cmd.append('--psk')
        
        # Hidden SSID
        if config.get('hidden'):
            cmd.append('--hidden')
        
        # MAC filtering
        if config.get('macFilter'):
            cmd.append('--mac-filter')
            if config.get('macFilterAccept'):
                cmd.extend(['--mac-filter-accept', config['macFilterAccept']])
        
        # Redirect to localhost
        if config.get('redirectToLocalhost'):
            cmd.append('--redirect-to-localhost')
        
        # Hostapd debug level
        if config.get('hostapdDebug'):
            cmd.extend(['--hostapd-debug', str(config['hostapdDebug'])])
        
        # Isolate clients
        if config.get('isolate'):
            cmd.append('--isolate-clients')
        
        # IEEE 802.11n
        if config.get('ieee80211n'):
            cmd.append('--ieee80211n')
        
        # IEEE 802.11ac
        if config.get('ieee80211ac'):
            cmd.append('--ieee80211ac')
        
        # HT capabilities
        if config.get('htCapab'):
            cmd.extend(['--ht_capab', config['htCapab']])
        
        # VHT capabilities
        if config.get('vhtCapab'):
            cmd.extend(['--vht_capab', config['vhtCapab']])
        
        # Country code
        if config.get('country'):
            cmd.extend(['--country', config['country']])
        
        # Frequency band
        if config.get('freqBand'):
            cmd.extend(['--freq-band', str(config['freqBand'])])
        
        # Driver
        if config.get('driver'):
            cmd.extend(['--driver', config['driver']])
        
        # No virtual interface
        if config.get('noVirt'):
            cmd.append('--no-virt')
        
        # No haveged
        if config.get('noHaveged'):
            cmd.append('--no-haveged')
        
        # Fix unmanaged
        if config.get('fixUnmanaged'):
            cmd.append('--fix-unmanaged')
        
        # MAC address
        if config.get('mac'):
            cmd.extend(['--mac', config['mac']])
        
        # DHCP DNS
        if config.get('dhcpDns'):
            cmd.extend(['--dhcp-dns', config['dhcpDns']])
        
        # Gateway (non-bridging)
        if config.get('gateway'):
            cmd.extend(['-g', config['gateway']])
        
        # No DNS
        if config.get('noDns'):
            cmd.append('--no-dns')
        
        # No dnsmasq
        if config.get('noDnsmasq'):
            cmd.append('--no-dnsmasq')
        
        # DNS with /etc/hosts
        if config.get('dnsHosts'):
            cmd.append('-d')
        
        # Additional hosts file
        if config.get('hostsFile'):
            cmd.extend(['-e', config['hostsFile']])
        
        # Daemon mode
        if config.get('daemon'):
            cmd.append('--daemon')
            
            # PID file for daemon
            if config.get('pidfile'):
                cmd.extend(['--pidfile', config['pidfile']])
                self.pid_file = config['pidfile']
            else:
                # Use default PID file
                self.pid_file = f'/var/run/create_ap_{config.get("wifiInterface", "wlan0")}.pid'
                cmd.extend(['--pidfile', self.pid_file])
            
            # Log file for daemon
            if config.get('logfile'):
                cmd.extend(['--logfile', config['logfile']])
        
        # Required parameters
        cmd.append(config.get('wifiInterface', 'wlan0'))
        
        # Internet interface (optional)
        if config.get('internetInterface') and not config.get('noInternet'):
            cmd.append(config['internetInterface'])
        
        # SSID
        cmd.append(config.get('ssid', 'OrangePi-Hotspot'))
        
        # Password (optional)
        if config.get('password'):
            cmd.append(config['password'])
        
        return cmd
    
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
                cmd = self.build_command(config)
                
                # Verify WiFi interface exists and supports AP mode
                wifi_iface = config.get('wifiInterface', 'wlan0')
                if not self.verify_wifi_interface(wifi_iface):
                    return {
                        'success': False,
                        'error': f'WiFi interface {wifi_iface} not found or does not support AP mode'
                    }
                
                # Start the process
                if config.get('daemon'):
                    # Daemon mode - process will detach
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        return {
                            'success': False,
                            'error': 'Failed to start daemon',
                            'details': result.stderr or result.stdout
                        }
                    
                    # Wait for PID file to be created
                    time.sleep(2)
                    
                    # Read PID from file
                    if self.pid_file and os.path.exists(self.pid_file):
                        with open(self.pid_file, 'r') as f:
                            pid = int(f.read().strip())
                        
                        if self.is_process_running(pid):
                            self.process = psutil.Process(pid)
                            self.is_running = True
                            self.start_time = time.time()
                            self.config = config
                            self.save_state()
                            
                            return {
                                'success': True,
                                'command': ' '.join(cmd),
                                'pid': pid,
                                'mode': 'daemon'
                            }
                    
                    return {
                        'success': False,
                        'error': 'Daemon started but PID file not found'
                    }
                else:
                    # Normal mode - keep process attached
                    self.process = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True
                    )
                    
                    # Wait a bit and check if process is still running
                    time.sleep(2)
                    if self.process.poll() is not None:
                        stdout, stderr = self.process.communicate()
                        return {
                            'success': False,
                            'error': 'create_ap failed to start',
                            'details': stderr or stdout
                        }
                    
                    self.is_running = True
                    self.start_time = time.time()
                    self.config = config
                    self.save_state()
                    
                    # Start log monitoring thread
                    threading.Thread(target=self.monitor_logs, daemon=True).start()
                    
                    return {
                        'success': True,
                        'command': ' '.join(cmd),
                        'pid': self.process.pid,
                        'mode': 'attached'
                    }
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def verify_wifi_interface(self, interface):
        """Verify that the interface exists and supports AP mode"""
        try:
            # Check if interface exists
            if not os.path.exists(f'/sys/class/net/{interface}'):
                return False
            
            # Check if it's a wireless interface
            if not os.path.exists(f'/sys/class/net/{interface}/wireless'):
                return False
            
            # Check if interface supports AP mode using iw
            result = subprocess.run(
                ['iw', 'list'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            # Look for AP mode support
            return 'AP' in result.stdout or 'AP/VLAN' in result.stdout
            
        except Exception as e:
            print(f"Error verifying interface: {e}")
            return False
    
    def monitor_logs(self):
        """Monitor create_ap output"""
        if not self.process:
            return
        
        try:
            for line in self.process.stdout:
                self.log_buffer.append({
                    'timestamp': datetime.now().isoformat(),
                    'message': line.strip()
                })
                # Keep only last 100 lines
                if len(self.log_buffer) > 100:
                    self.log_buffer.pop(0)
        except Exception as e:
            print(f"Error monitoring logs: {e}")
    
    def stop(self, interface=None):
        """Stop the WiFi hotspot"""
        with self.lock:
            if not self.is_running:
                # Try to find and stop any running instances
                instances = self.find_running_instances()
                if instances:
                    for inst in instances:
                        try:
                            subprocess.run(
                                ['create_ap', '--stop', str(inst['pid'])],
                                timeout=10
                            )
                        except:
                            pass
                    self.clear_state()
                    return {'success': True, 'message': 'Stopped orphaned instances'}
                
                return {'success': False, 'error': 'Hotspot is not running'}
            
            try:
                # If daemon mode, use create_ap --stop
                if self.config.get('daemon'):
                    wifi_iface = self.config.get('wifiInterface', 'wlan0')
                    result = subprocess.run(
                        ['create_ap', '--stop', wifi_iface],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        # Try with PID
                        if self.process:
                            subprocess.run(
                                ['create_ap', '--stop', str(self.process.pid)],
                                timeout=10
                            )
                else:
                    # Normal mode - terminate process
                    if self.process:
                        # Send SIGINT first (graceful shutdown)
                        self.process.send_signal(signal.SIGINT)
                        try:
                            self.process.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            # Force kill if graceful shutdown fails
                            self.process.kill()
                            self.process.wait()
                
                # Clean up PID file
                if self.pid_file and os.path.exists(self.pid_file):
                    try:
                        os.remove(self.pid_file)
                    except:
                        pass
                
                self.process = None
                self.is_running = False
                self.start_time = None
                self.log_buffer = []
                self.clear_state()
                
                return {'success': True}
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def get_status(self):
        """Get current hotspot status"""
        uptime = 0
        if self.is_running and self.start_time:
            uptime = int(time.time() - self.start_time)
        
        # Check if process is still alive
        if self.is_running and self.process:
            try:
                if isinstance(self.process, psutil.Process):
                    if not self.process.is_running():
                        self.is_running = False
                        self.start_time = None
                        self.clear_state()
                else:
                    if self.process.poll() is not None:
                        self.is_running = False
                        self.start_time = None
                        self.clear_state()
            except:
                pass
        
        return {
            'isRunning': self.is_running,
            'uptime': uptime,
            'config': self.config,
            'logs': self.log_buffer[-20:] if self.log_buffer else [],
            'pid': self.process.pid if self.process else None
        }
    
    def get_connected_clients(self):
        """Get list of connected clients"""
        clients = []
        
        if not self.is_running:
            return clients
        
        try:
            # Use create_ap --list-clients if in daemon mode
            if self.config.get('daemon'):
                wifi_iface = self.config.get('wifiInterface', 'wlan0')
                result = subprocess.run(
                    ['create_ap', '--list-clients', wifi_iface],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    for line in lines:
                        # Parse client info
                        match = re.search(r'([0-9a-fA-F:]{17})\s+(\d+\.\d+\.\d+\.\d+)?', line)
                        if match:
                            mac = match.group(1)
                            ip = match.group(2) if match.group(2) else None
                            clients.append({
                                'mac': mac,
                                'ip': ip,
                                'hostname': self.get_hostname(ip) if ip else 'Unknown'
                            })
            else:
                # Get the AP interface name
                ap_interface = self.config.get('wifiInterface', 'wlan0')
                
                # Try to get clients from iw
                result = subprocess.run(
                    ['iw', 'dev', ap_interface, 'station', 'dump'],
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                
                if result.returncode == 0:
                    current_client = {}
                    for line in result.stdout.split('\n'):
                        line = line.strip()
                        if line.startswith('Station'):
                            if current_client:
                                clients.append(current_client)
                            mac = line.split()[1]
                            current_client = {'mac': mac, 'ip': None, 'hostname': None}
                        elif 'signal:' in line and current_client:
                            signal_strength = line.split(':')[1].strip().split()[0]
                            current_client['signal'] = signal_strength
                    
                    if current_client:
                        clients.append(current_client)
                
                # Try to get IP addresses from DHCP leases or ARP
                for client in clients:
                    ip = self.get_client_ip(client['mac'])
                    if ip:
                        client['ip'] = ip
                        client['hostname'] = self.get_hostname(ip)
        
        except Exception as e:
            print(f"Error getting clients: {e}")
        
        return clients
    
    def get_client_ip(self, mac):
        """Get IP address for MAC address"""
        try:
            # Try ARP table first
            result = subprocess.run(
                ['arp', '-n'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            for line in result.stdout.split('\n'):
                if mac.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 1:
                        return parts[0]
            
            # Try DHCP leases file
            lease_files = [
                '/var/lib/misc/dnsmasq.leases',
                '/var/lib/dhcp/dhcpd.leases'
            ]
            
            for lease_file in lease_files:
                if os.path.exists(lease_file):
                    with open(lease_file, 'r') as f:
                        for line in f:
                            if mac.lower() in line.lower():
                                parts = line.split()
                                if len(parts) >= 3:
                                    return parts[2]
        except Exception as e:
            print(f"Error getting client IP: {e}")
        
        return None
    
    def get_hostname(self, ip):
        """Try to get hostname for IP"""
        if not ip:
            return "Unknown"
        
        try:
            result = subprocess.run(
                ['nslookup', ip],
                capture_output=True,
                text=True,
                timeout=1
            )
            
            for line in result.stdout.split('\n'):
                if 'name =' in line:
                    return line.split('name =')[1].strip().rstrip('.')
        except:
            pass
        
        return f"Device-{ip.split('.')[-1]}"
    
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
        except Exception as e:
            print(f"Error getting stats: {e}")
        
        return {
            'txBytes': 0,
            'rxBytes': 0,
            'txPackets': 0,
            'rxPackets': 0
        }
    
    def get_last_config(self):
        """Get last saved configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading last config: {e}")
        
        return None

# Global hotspot manager instance
manager = HotspotManager()

@app.route('/')
def index():
    """Serve the main page"""
    return render_template('index.html')

@app.route('/api/start', methods=['POST'])
def start_hotspot():
    """Start the WiFi hotspot"""
    config = request.json
    result = manager.start(config)
    return jsonify(result)

@app.route('/api/stop', methods=['POST'])
def stop_hotspot():
    """Stop the WiFi hotspot"""
    result = manager.stop()
    return jsonify(result)

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get hotspot status"""
    status = manager.get_status()
    clients = manager.get_connected_clients()
    
    # Get interface stats
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
    """Get available network interfaces with proper WiFi detection"""
    try:
        interfaces = []
        
        # Get all network interfaces
        net_if = psutil.net_if_addrs()
        net_stats = psutil.net_if_stats()
        
        for iface_name in net_if.keys():
            if iface_name == 'lo':
                continue
            
            # Check if interface is up
            if iface_name not in net_stats or not net_stats[iface_name].isup:
                continue
            
            iface_info = {
                'name': iface_name,
                'type': 'unknown',
                'isWireless': False,
                'supportsAP': False
            }
            
            # Check if it's a wireless interface
            if os.path.exists(f'/sys/class/net/{iface_name}/wireless'):
                iface_info['type'] = 'wifi'
                iface_info['isWireless'] = True
                
                # Check if it supports AP mode
                try:
                    result = subprocess.run(
                        ['iw', 'list'],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    
                    if 'AP' in result.stdout or 'AP/VLAN' in result.stdout:
                        iface_info['supportsAP'] = True
                except:
                    pass
            
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

@app.route('/api/command-preview', methods=['POST'])
def get_command_preview():
    """Get command preview without executing"""
    config = request.json
    cmd = manager.build_command(config)
    return jsonify({'command': ' '.join(cmd)})

@app.route('/api/check-prerequisites', methods=['GET'])
def check_prerequisites():
    """Check system prerequisites"""
    errors = manager.check_prerequisites()
    return jsonify({
        'success': len(errors) == 0,
        'errors': errors
    })

@app.route('/api/last-config', methods=['GET'])
def get_last_config():
    """Get last saved configuration"""
    config = manager.get_last_config()
    return jsonify({'config': config})

@app.route('/api/running-instances', methods=['GET'])
def get_running_instances():
    """Get all running create_ap instances"""
    instances = manager.find_running_instances()
    return jsonify({'instances': instances})
    
@app.route('/api/logs', methods=['GET'])
def get_logs():
    """Get recent logs"""
    logs = manager.log_buffer[-50:] if manager.log_buffer else []
    
    # Also try to read from log file if daemon mode
    if manager.config.get('daemon') and manager.config.get('logfile'):
        try:
            logfile = manager.config['logfile']
            if os.path.exists(logfile):
                with open(logfile, 'r') as f:
                    lines = f.readlines()[-50:]
                    for line in lines:
                        logs.append({
                            'timestamp': datetime.now().isoformat(),
                            'message': line.strip()
                        })
        except Exception as e:
            print(f"Error reading log file: {e}")
    
    return jsonify({'logs': logs})    

if __name__ == '__main__':
    # Check if running as root
    if os.geteuid() != 0:
        print("=" * 60)
        print("ERROR: This application MUST be run as root!")
        print("=" * 60)
        print("\nPlease run with:")
        print("  sudo python3 app.py")
        print("\nOr for production:")
        print("  sudo gunicorn -w 1 -b 0.0.0.0:5000 app:app")
        print("=" * 60)
        exit(1)
    
    # Check prerequisites
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
    
    # Check for existing state
    if manager.is_running:
        print(f"✅ Restored connection to running hotspot")
        print(f"   SSID: {manager.config.get('ssid', 'Unknown')}")
        print(f"   Interface: {manager.config.get('wifiInterface', 'Unknown')}")
    else:
        print("ℹ️  No active hotspot found")
    
    print("=" * 60)
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=False)
