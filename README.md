[🇺🇸 English version](README-EN.md)

# Trình quản lý WiFi Hotspot cho Orange Pi

Giao diện web hiện đại để quản lý WiFi Hotspot trên Orange Pi bằng **hostapd** và **dnsmasq**.  
Ứng dụng cung cấp khả năng giám sát thời gian thực, cấu hình đầy đủ, hỗ trợ các chuẩn WiFi 4/5/6 và giao diện trực quan.

![WiFi Hotspot Manager](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![WiFi](https://img.shields.io/badge/WiFi-4%2F5%2F6-orange.svg)

## 🌟 Tính năng

### 📡 Cấu hình WiFi toàn diện
- **Bảo mật WPA**: WPA, WPA2 và WPA3 (SAE)
- **Chọn kênh**: 2.4 GHz (1–13) và 5 GHz (36–165)
- **Băng tần**: 2.4 GHz / 5 GHz
- **Mã quốc gia**: Regulatory domain
- **Chuẩn WiFi**: 802.11n / 802.11ac / 802.11ax

### 🌐 Chia sẻ mạng
- NAT Mode
- Bridge Mode
- Standalone Mode
- Custom Gateway
- DHCP Server

### 📊 Giám sát
- Uptime
- Client kết nối
- TX/RX
- Log sự kiện

## 🚀 Cài đặt

```bash
git clone https://github.com/thanhtantran/opi4pro_wifi6_hotspot.git
cd opi4pro_wifi6_hotspot
sudo apt update
sudo apt install hostapd dnsmasq python3-pip
pip3 install -r requirements.txt
sudo systemctl stop hostapd
sudo systemctl disable hostapd
sudo python3 app.py
```

Truy cập:
http://IP_ORANGE_PI:5000

## 📄 Giấy phép
MIT License

---
Orange Pi Vietnam
