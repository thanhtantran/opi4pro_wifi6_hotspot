# WiFi Hotspot Manager for Orange Pi

A modern web-based interface for managing WiFi hotspots on Orange Pi 4Pro using the `create_ap` script. Features real-time monitoring, comprehensive configuration options, and an intuitive user interface.

![WiFi Hotspot Manager](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🌟 Features

### 📡 Comprehensive WiFi Configuration
- **WPA Security**: WPA, WPA2, or WPA/WPA2 mixed mode
- **Channel Selection**: Auto or manual (1-11) with frequency display
- **Frequency Bands**: 2.4 GHz and 5 GHz support
- **Country Code**: Regulatory domain configuration
- **Advanced Standards**: IEEE 802.11n (HT) and 802.11ac (VHT)

### 🌐 Network Sharing Options
- **NAT Mode**: Network Address Translation (default)
- **Bridge Mode**: Direct bridging to existing network
- **Standalone Mode**: No internet sharing (isolated AP)
- **Custom Gateway**: Configure custom gateway IP addresses

### 📊 Real-Time Monitoring
- **Live Statistics**: Uptime, connected clients, TX/RX rates
- **Client Information**: View connected devices with IP, MAC, and hostname
- **Traffic Monitoring**: Track data transfer rates and total bandwidth usage
- **Activity Logs**: Timestamped event logging

### ⚙️ Advanced Options
- Hidden network (SSID broadcast control)
- Client isolation (prevent client-to-client communication)
- MAC address filtering
- Virtual interface control
- DNS server configuration
- Daemon mode support

## 📸 Screenshots

### Main Interface
The dashboard shows all configuration options and real-time statistics.

### Live Monitoring
Track connected clients and bandwidth usage in real-time.

## 🚀 Quick Start

### Prerequisites

- Orange Pi 4Pro
- Python 3.12 or higher
- `create_ap` script installed
- Root/sudo access

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/thanhtantran/opi4pro_wifi6_hotspot.git
cd opi4pro_wifi6_hotspot

```

2. **Install Python dependencies**
```bash
pip3 install -r requirements.txt
```

3. **Install create_ap** (in the OS of Orange PI 4 Pro already had this app, only install if it is not already installed)
```bash
git clone https://github.com/oblique/create_ap
cd create_ap
sudo make install
cd ..
```

4. **Run the application**
```bash
sudo python3 app.py
```

5. **Access the web interface**
Open your browser and navigate to:
```
http://localhost:5000
```
Or from another device on the network:
```
http://your-orange-pi-ip:5000
```

## 📁 Project Structure

```
wifi-hotspot-manager/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Web interface
├── README.md             # This file
└── LICENSE               # MIT License
```

## 🔧 Configuration Options

### Basic Settings
- **WiFi Interface**: Select your wireless adapter (e.g., wlan0)
- **Internet Interface**: Select interface with internet connection (e.g., eth0)
- **SSID**: Network name (visible to clients)
- **Password**: WPA/WPA2 password (minimum 8 characters)

### Wireless Settings
- **WPA Version**: 1, 2, or 1+2 (both)
- **Channel**: Auto or specific channel (1-11)
- **Frequency Band**: 2.4 GHz or 5 GHz
- **Country Code**: Two-letter country code (e.g., US, GB, VN)

### Network Settings
- **Sharing Method**: NAT, Bridge, or None
- **Gateway IP**: Default 192.168.12.1

### Advanced Options
- **Hidden Network**: Don't broadcast SSID
- **Isolate Clients**: Prevent client-to-client communication
- **No Virtual Interface**: Use physical interface directly
- **MAC Filtering**: Enable MAC address whitelist
- **IEEE 802.11n/ac**: Enable high-throughput modes
- **Daemon Mode**: Run in background
- **No Haveged**: Disable entropy generator
- **Disable DNS**: Turn off DNS server

## 🖥️ API Endpoints

### GET `/`
Returns the main web interface

### GET `/api/interfaces`
Returns list of available network interfaces
```json
{
  "interfaces": [
    {"name": "wlan0", "type": "wifi", "isup": false},
    {"name": "eth0", "type": "ethernet", "isup": true}
  ]
}
```

### POST `/api/start`
Start the WiFi hotspot with provided configuration
```json
{
  "wifiInterface": "wlan0",
  "internetInterface": "eth0",
  "ssid": "MyHotspot",
  "password": "MyPassword123",
  ...
}
```

### POST `/api/stop`
Stop the currently running hotspot

### GET `/api/status`
Get current hotspot status, connected clients, and statistics

## 🛠️ Troubleshooting

### WiFi interface not showing up
```bash
# Check if interface exists
ip link show

# Unblock WiFi if needed
sudo rfkill unblock wifi
```

### NetworkManager conflicts
```bash
# Stop NetworkManager temporarily
sudo systemctl stop NetworkManager

# Or configure it to ignore your WiFi interface
sudo nano /etc/NetworkManager/NetworkManager.conf
# Add:
[keyfile]
unmanaged-devices=interface-name:wlan0
```

### Permission denied
Make sure you're running with sudo:
```bash
sudo python3 app.py
```

### create_ap not found
```bash
# Install create_ap
git clone https://github.com/oblique/create_ap
cd create_ap
sudo make install
```

### WiFi adapter doesn't support AP mode
```bash
# Check adapter capabilities
iw list | grep -A 10 "Supported interface modes"
# Look for "AP" in the output
```

## 🔒 Security Considerations

- **Production Use**: For production deployments, add authentication to the web interface
- **HTTPS**: Use SSL/TLS certificates for encrypted communication
- **Firewall**: Restrict access to port 5000 to trusted networks
- **Strong Passwords**: Always use strong WPA2 passwords (minimum 8 characters)
- **Client Isolation**: Enable for public hotspots to enhance security

## 🚀 Running as a Service

Create a systemd service for automatic startup:

```bash
sudo nano /etc/systemd/system/wifi-hotspot.service
```

Add the following content:
```ini
[Unit]
Description=WiFi Hotspot Manager
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/wifi-hotspot-manager
ExecStart=/usr/bin/python3 /path/to/wifi-hotspot-manager/app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi-hotspot
sudo systemctl start wifi-hotspot
```

## 📝 Usage Examples

### Basic Hotspot with Internet Sharing
```
SSID: MyHotspot
Password: MySecurePass123
WiFi Interface: wlan0
Internet Interface: eth0
Method: NAT
```

### Hidden Network for Security
```
SSID: SecretNetwork
Password: VerySecurePass456
Hidden Network: ✓
Isolate Clients: ✓
```

### High-Performance 5GHz Hotspot
```
SSID: FastAP
Frequency Band: 5 GHz
IEEE 802.11ac: ✓
Channel: Auto
```

### Standalone AP (No Internet)
```
SSID: LocalNetwork
Sharing Method: None
Gateway: 192.168.12.1
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [create_ap](https://github.com/oblique/create_ap) - The excellent WiFi AP creation script
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Lucide Icons](https://lucide.dev/) - Beautiful icon set
- [psutil](https://github.com/giampaolo/psutil) - Cross-platform system utilities

## 📧 Support

If you encounter any issues or have questions:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [existing issues](https://github.com/yourusername/wifi-hotspot-manager/issues)
3. Create a new issue with detailed information

## 🗺️ Roadmap

- [ ] Add authentication for web interface
- [ ] HTTPS support with SSL certificates
- [ ] Save/load configuration presets
- [ ] Bandwidth limiting per client
- [ ] QR code generation for easy connection
- [ ] Email notifications for events
- [ ] Multi-language support
- [ ] Docker containerization

## ⭐ Star History

If you find this project useful, please consider giving it a star!

---

**Made with ❤️ from [Orange Pi Vietnam](https://orangepi.vn)**
