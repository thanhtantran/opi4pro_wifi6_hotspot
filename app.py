#!/usr/bin/env python3
"""
WiFi Hotspot Manager for Orange Pi
Manages create_ap commands and monitors hotspot status
"""

from flask import Flask, render_template, request, jsonify
import subprocess
import threading
import time
import re
import os
import signal
import psutil
from datetime import datetime

app = Flask(__name__)

class HotspotManager:
    def __init__(self):
        self.process = None
        self.is_running = False
        self.start_time = None
        self.config = {}
        self.lock = threading.Lock()
        
    def build_command(self, config):
        """Build create_ap command from configuration"""
        cmd = ['create_ap']
        
        # Add options
        if config.get('encryption') and config['encryption'] != 'WPA2':
            cmd.extend(['--encryption', config['encryption']])
        
        if config.get('channel') and config['channel'] != 'auto':
            cmd.extend(['-c', config['channel']])
        
        if config.get('bandwidth') and config['bandwidth'] != '20':
            cmd.extend(['--bandwidth', config['bandwidth']])
        
        if config.get('hidden'):
            cmd.append('--hidden')
        
        if config.get('isolate'):
            cmd.append('--isolate-clients')
        
        if config.get('noVirt'):
            cmd.append('--no-virt')
        
        # Add required parameters
        cmd.append(config.get('wifiInterface', 'wlan0'))
        
        if config.get('internetInterface'):
            cmd.append(config['internetInterface'])
        
        cmd.append(config.get('ssid', 'OrangePi-Hotspot'))
        
        if config.get('password'):
            cmd.append(config['password'])
        
        return cmd
    
    def start(self, config):
        """Start the WiFi hotspot"""
        with self.lock:
            if self.is_running:
                return {'success': False, 'error': 'Hotspot is already running'}
            
            try:
                cmd = self.build_command(config)
                
                print(f"Executing command: {' '.join(cmd)}")
                
                # Check if create_ap exists
                try:
                    subprocess.run(['which', 'create_ap'], check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    return {
                        'success': False, 
                        'error': 'create_ap command not found. Please install it first.'
                    }
                
                # Start the process
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True
                )
                
                # Wait a moment to check if process started successfully
                time.sleep(1)
                
                if self.process.poll() is not None:
                    # Process already exited, get error
                    stderr = self.process.stderr.read()
                    return {
                        'success': False,
                        'error': f'create_ap failed to start: {stderr}'
                    }
                
                self.is_running = True
                self.start_time = time.time()
                self.config = config
                
                print(f"Hotspot started with PID: {self.process.pid}")
                
                return {
                    'success': True,
                    'command': ' '.join(cmd),
                    'pid': self.process.pid
                }
                
            except Exception as e:
                print(f"Error starting hotspot: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': str(e)}
    
    def stop(self):
        """Stop the WiFi hotspot"""
        with self.lock:
            if not self.is_running:
                return {'success': False, 'error': 'Hotspot is not running'}
            
            try:
                if self.process:
                    # Terminate the process
                    self.process.terminate()
                    try:
                        self.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        self.process.kill()
                    
                    self.process = None
                
                self.is_running = False
                self.start_time = None
                
                return {'success': True}
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def get_status(self):
        """Get current hotspot status"""
        uptime = 0
        if self.is_running and self.start_time:
            uptime = int(time.time() - self.start_time)
        
        return {
            'isRunning': self.is_running,
            'uptime': uptime,
            'config': self.config
        }
    
    def get_connected_clients(self):
        """Get list of connected clients"""
        clients = []
        
        if not self.is_running:
            return clients
        
        try:
            # Try to get clients from arp table
            result = subprocess.run(
                ['arp', '-n'],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            lines = result.stdout.split('\n')[1:]  # Skip header
            
            for line in lines:
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[0]
                        mac = parts[2]
                        
                        # Filter for hotspot subnet (typically 192.168.12.x)
                        if ip.startswith('192.168.12.') and mac != '<incomplete>':
                            hostname = self.get_hostname(ip)
                            clients.append({
                                'ip': ip,
                                'mac': mac,
                                'hostname': hostname
                            })
        
        except Exception as e:
            print(f"Error getting clients: {e}")
        
        return clients
    
    def get_hostname(self, ip):
        """Try to get hostname for IP"""
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
    """Get available network interfaces"""
    try:
        addrs = psutil.net_if_addrs()
        stats = psutil.net_if_stats()
        
        interfaces = []
        for iface_name, iface_addrs in addrs.items():
            # Skip loopback and virtual interfaces
            if iface_name in ['lo', 'ip_vti0', 'ip6_vti0', 'sit0', 'ip6tnl0']:
                continue
            
            # Skip if interface doesn't exist in stats
            if iface_name not in stats:
                continue
                
            iface_type = 'unknown'
            
            # Detect WiFi interfaces
            if 'wlan' in iface_name or 'wlp' in iface_name or 'wlx' in iface_name:
                iface_type = 'wifi'
            # Detect Ethernet interfaces
            elif 'eth' in iface_name or 'enp' in iface_name or 'eno' in iface_name:
                iface_type = 'ethernet'
            else:
                # Skip other interface types
                continue
            
            # Include interface even if it's down (for WiFi interfaces especially)
            # since they can be brought up for AP mode
            interfaces.append({
                'name': iface_name,
                'type': iface_type,
                'isup': stats[iface_name].isup
            })
        
        # Sort interfaces: wifi first, then ethernet
        interfaces.sort(key=lambda x: (x['type'] != 'wifi', x['name']))
        
        return jsonify({'interfaces': interfaces})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/command-preview', methods=['POST'])
def get_command_preview():
    """Get command preview without executing"""
    config = request.json
    cmd = manager.build_command(config)
    return jsonify({'command': ' '.join(cmd)})

if __name__ == '__main__':
    # Check if running as root
    if os.geteuid() != 0:
        print("WARNING: This script should be run as root to manage WiFi hotspots")
        print("Try: sudo python3 app.py")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)