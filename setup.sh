#!/bin/bash

# WiFi Hotspot Manager Setup Script
# For Orange Pi and compatible Linux systems

echo "============================================"
echo "  WiFi Hotspot Manager Setup"
echo "============================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script should be run as root (use sudo)"
    exit 1
fi

echo "📦 Step 1: Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip git iw hostapd dnsmasq

echo ""
echo "📦 Step 2: Installing Python dependencies..."
pip3 install -r requirements.txt

echo ""
echo "📡 Step 3: Checking for create_ap..."
if ! command -v create_ap &> /dev/null; then
    echo "create_ap not found. Installing..."
    
    # Clone and install create_ap
    cd /tmp
    git clone https://github.com/oblique/create_ap
    cd create_ap
    make install
    cd -
    rm -rf /tmp/create_ap
    
    echo "✓ create_ap installed successfully"
else
    echo "✓ create_ap is already installed"
fi

echo ""
echo "🔧 Step 4: Creating templates directory..."
mkdir -p templates
echo "✓ Templates directory ready"

echo ""
echo "🌐 Step 5: Checking network interfaces..."
echo "Available WiFi interfaces:"
ip link show | grep -E "wlan|wlp" || echo "  No WiFi interface found!"
echo ""
echo "Available Ethernet interfaces:"
ip link show | grep -E "eth|enp" || echo "  No Ethernet interface found!"

echo ""
echo "🔓 Step 6: Unblocking WiFi (if blocked)..."
rfkill unblock wifi
echo "✓ WiFi unblocked"

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo "📝 Next steps:"
echo "  1. Make sure index.html is in the templates/ directory"
echo "  2. Run the application: sudo python3 app.py"
echo "  3. Access the web interface at http://localhost:5000"
echo ""
echo "💡 Tips:"
echo "  - Check WiFi adapter supports AP mode: iw list | grep 'AP'"
echo "  - If NetworkManager conflicts, stop it: systemctl stop NetworkManager"
echo "  - View logs in real-time: tail -f /var/log/syslog"
echo ""
echo "🎉 Happy hotspot managing!"
echo ""