[vn Tiếng Việt](README.md)

# WiFi Hotspot Manager for Orange Pi

A modern web-based interface for managing WiFi hotspots on Orange Pi using **hostapd** and **dnsmasq**. Features real-time monitoring, comprehensive configuration options, full support for WiFi 4/5/6 standards, and an intuitive user interface.

![WiFi Hotspot Manager](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![WiFi](https://img.shields.io/badge/WiFi-4%2F5%2F6-orange.svg)

## 🌟 Features

### 📡 Comprehensive WiFi Configuration
- **WPA Security**: WPA, WPA2, and WPA3 (SAE) support
- **Channel Selection**: Full channel support for 2.4 GHz (1-13) and 5 GHz (36-165)
- **Frequency Bands**: 2.4 GHz and 5 GHz with automatic channel selection
- **Country Code**: Regulatory domain configuration for proper compliance
- **WiFi Standards**: 
  - **802.11n (WiFi 4)**: Up to 600 Mbps
  - **802.11ac (WiFi 5)**: Up to 3.5 Gbps
  - **802.11ax (WiFi 6)**: Up to 9.6 Gbps (hardware dependent)

### 🌐 Network Sharing Options
- **NAT Mode**: Network Address Translation (default)
- **Bridge Mode**: Direct bridging to existing network
- **Standalone Mode**: No internet sharing (isolated AP)
- **Custom Gateway**: Configure custom gateway IP addresses
- **DHCP Server**: Built-in DHCP with configurable IP ranges

### 📊 Real-Time Monitoring
- **Live Statistics**: Uptime, connected clients, TX/RX rates
- **Client Information**: View connected devices with IP, MAC, hostname, and signal strength
- **Traffic Monitoring**: Track data transfer rates and total bandwidth usage
- **Activity Logs**: Timestamped event logging with client connection/disconnection events

### ⚙️ Advanced Options
- **Hidden Network**: SSID broadcast control
- **Client Isolation**: Prevent client-to-client communication (AP isolation)
- **MAC Address Filtering**: Whitelist-based access control
- **HT/VHT/HE Capabilities**: Fine-tune 802.11n/ac/ax parameters
- **DNS Configuration**: Custom DNS servers or disable DNS
- **Max Stations**: Limit maximum number of connected clients
- **PSK Mode**: Use pre-shared key (64 hex digits)

## 📸 Screenshots

### Main Interface
The dashboard shows all configuration options with collapsible advanced settings.

### Live Monitoring
Track connected clients with signal strength, bandwidth usage, and real-time statistics.

### Configuration Display
View current running configuration including WiFi standards, frequency, channel, and security settings.

## 🚀 Quick Start

### Prerequisites

- Orange Pi device (tested on Orange Pi 4 Pro)
- Python 3.12 or higher
- **hostapd** and **dnsmasq** installed
- Root/sudo access
- WiFi adapter with AP mode support (tested on Orange Pi 4 Pro)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/thanhtantran/opi4pro_wifi6_hotspot.git
cd opi4pro_wifi6_hotspot
```

2. **Install Python and hostapd dependencies**
```bash
sudo apt update
sudo apt install hostapd dnsmasq python3-pip
pip3 install -r requirements.txt
```

3. **Disable the hostapd service if any**
```
sudo systemctl stop hostapd
sudo systemctl disable hostapd
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

- [hostapd](https://w1.fi/hostapd) - The excellent WiFi AP app
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