[🇺🇸 English version](README-EN.md)

# Trình quản lý WiFi Hotspot cho Orange Pi

Giao diện web hiện đại để quản lý WiFi hotspot trên Orange Pi sử dụng **hostapd** và **dnsmasq**. Hỗ trợ giám sát thời gian thực, tùy chọn cấu hình toàn diện, hỗ trợ đầy đủ các chuẩn WiFi 4/5/6 và giao diện người dùng trực quan.

![WiFi Hotspot Manager](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![WiFi](https://img.shields.io/badge/WiFi-4%2F5%2F6-orange.svg)

## 🌟 Tính năng

### 📡 Cấu hình WiFi toàn diện

- **Bảo mật WPA**: Hỗ trợ WPA, WPA2 và WPA3 (SAE)
- **Chọn kênh**: Đầy đủ kênh cho 2.4 GHz (1-13) và 5 GHz (36-165)
- **Băng tần**: 2.4 GHz và 5 GHz với lựa chọn kênh tự động
- **Mã quốc gia**: Cấu hình miền quy định để tuân thủ pháp lý
- **Chuẩn WiFi**:
    - **802.11n (WiFi 4)**: Tối đa 600 Mbps
    - **802.11ac (WiFi 5)**: Tối đa 3.5 Gbps
    - **802.11ax (WiFi 6)**: Tối đa 9.6 Gbps (phụ thuộc phần cứng, đã thử nghiệm trên Orange Pi 4 Pro)


### 🌐 Tùy chọn chia sẻ mạng

- **Chế độ NAT**: Network Address Translation (mặc định)
- **Chế độ Bridge**: Bridge trực tiếp vào mạng hiện có
- **Chế độ độc lập**: Không chia sẻ internet (AP cô lập)
- **Gateway tùy chỉnh**: Cấu hình địa chỉ IP gateway tùy chỉnh
- **DHCP Server**: DHCP tích hợp với dải IP cấu hình được


### 📊 Giám sát thời gian thực

- **Thống kê trực tiếp**: Thời gian hoạt động, số client kết nối, tốc độ TX/RX
- **Thông tin client**: Xem thiết bị kết nối với IP, MAC, hostname và cường độ tín hiệu
- **Giám sát lưu lượng**: Theo dõi tốc độ truyền dữ liệu và tổng băng thông sử dụng
- **Nhật ký hoạt động**: Ghi nhật ký sự kiện theo dấu thời gian với các lần client kết nối/ngắt kết nối


### ⚙️ Tùy chọn nâng cao

- **Mạng ẩn**: Điều khiển broadcast SSID
- **Cô lập client**: Ngăn client giao tiếp với nhau (AP isolation)
- **Lọc địa chỉ MAC**: Kiểm soát truy cập dựa trên whitelist
- **Khả năng HT/VHT/HE**: Tinh chỉnh các tham số 802.11n/ac/ax
- **Cấu hình DNS**: DNS tùy chỉnh hoặc tắt DNS
- **Số client tối đa**: Giới hạn số lượng client kết nối tối đa
- **Chế độ PSK**: Dùng khóa chia sẻ trước (64 ký tự hex)


## 📸 Ảnh màn hình

### Giao diện chính

Dashboard hiển thị tất cả tùy chọn cấu hình với phần thiết lập nâng cao có thể thu gọn.

### Giám sát trực tiếp

Theo dõi client đang kết nối với cường độ tín hiệu, băng thông sử dụng và thống kê thời gian thực.

### Hiển thị cấu hình

Xem cấu hình đang chạy hiện tại bao gồm chuẩn WiFi, tần số, kênh và thiết lập bảo mật.

## 🚀 Bắt đầu nhanh

### Yêu cầu

- Thiết bị Orange Pi (đã kiểm thử trên Orange Pi 4 Pro)
- Python 3.12 hoặc cao hơn
- Đã cài **hostapd** và **dnsmasq**
- Quyền root/sudo
- WiFi adapter hỗ trợ chế độ AP (đã kiểm thử trên Orange Pi 4 Pro)


### Cài đặt

1. **Clone repo**
```bash
git clone https://github.com/thanhtantran/opi4pro_wifi6_hotspot.git
cd opi4pro_wifi6_hotspot
```

2. **Cài Python và các phụ thuộc hostapd**
```bash
sudo apt update
sudo apt install hostapd dnsmasq python3-pip
pip3 install -r requirements.txt
```

3. **Tắt service hostapd nếu có**
```
sudo systemctl stop hostapd
sudo systemctl disable hostapd
```

4. **Chạy ứng dụng**
```bash
sudo python3 app.py
```

5. **Truy cập giao diện web**

Mở trình duyệt và truy cập:

```
http://localhost:5000
```

Hoặc từ thiết bị khác trong mạng:

```
http://your-orange-pi-ip:5000
```


## 📁 Cấu trúc dự án

```text
opi4pro_wifi6_hotspot/
├── app.py                 # Ứng dụng backend Flask
├── requirements.txt       # Các gói phụ thuộc Python
├── templates/
│   └── index.html        # Giao diện web
├── README.md             # File này
└── LICENSE               # Giấy phép MIT
```


## 🔧 Tùy chọn cấu hình

### Thiết lập cơ bản

- **WiFi Interface**: Chọn adapter không dây (vd: wlan0)
- **Internet Interface**: Chọn interface có kết nối internet (vd: eth0)
- **SSID**: Tên mạng (hiện với client)
- **Password**: Mật khẩu WPA/WPA2 (tối thiểu 8 ký tự)


### Thiết lập không dây

- **Phiên bản WPA**: 1, 2 hoặc 1+2 (cả hai)
- **Kênh**: Auto hoặc kênh cụ thể (1-11)
- **Băng tần**: 2.4 GHz hoặc 5 GHz
- **Mã quốc gia**: Mã quốc gia 2 ký tự (vd: US, GB, VN)


### Thiết lập mạng

- **Phương thức chia sẻ**: NAT, Bridge hoặc None
- **Gateway IP**: Mặc định 192.168.12.1


### Tùy chọn nâng cao

- **Hidden Network**: Không broadcast SSID
- **Isolate Clients**: Ngăn client giao tiếp với nhau
- **No Virtual Interface**: Dùng trực tiếp interface vật lý
- **MAC Filtering**: Bật whitelist địa chỉ MAC
- **IEEE 802.11n/ac**: Bật các chế độ thông lượng cao
- **Daemon Mode**: Chạy nền
- **No Haveged**: Tắt trình sinh entropy
- **Disable DNS**: Tắt DNS server


## 🖥️ API Endpoints

### GET `/`

Trả về giao diện web chính.

### GET `/api/interfaces`

Trả về danh sách các network interface hiện có.

```json
{
  "interfaces": [
    {"name": "wlan0", "type": "wifi", "isup": false},
    {"name": "eth0", "type": "ethernet", "isup": true}
  ]
}
```


### POST `/api/start`

Khởi động WiFi hotspot với cấu hình được cung cấp.

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

Dừng hotspot đang chạy.

### GET `/api/status`

Lấy trạng thái hotspot hiện tại, client kết nối và thống kê.

## 🔒 Lưu ý bảo mật

- **Dùng trong môi trường production**: Với triển khai production, hãy thêm xác thực cho giao diện web.
- **HTTPS**: Dùng chứng chỉ SSL/TLS để mã hóa kết nối.
- **Firewall**: Giới hạn truy cập port 5000 cho các mạng tin cậy.
- **Mật khẩu mạnh**: Luôn dùng mật khẩu WPA2 mạnh (tối thiểu 8 ký tự).
- **Cô lập client**: Bật cho các hotspot công cộng để tăng bảo mật.


## 🚀 Chạy như service

Tạo systemd service để tự động khởi động:

```bash
sudo nano /etc/systemd/system/wifi-hotspot.service
```

Thêm nội dung sau:

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

Bật và khởi động service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable wifi-hotspot
sudo systemctl start wifi-hotspot
```


## 🤝 Đóng góp

Rất hoan nghênh đóng góp! Hãy thoải mái gửi Pull Request.

1. Fork repository
2. Tạo nhánh tính năng (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên nhánh (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📄 Giấy phép

Dự án này được cấp phép theo MIT License - xem file [LICENSE](LICENSE) để biết chi tiết.

## 🙏 Lời cảm ơn

- [hostapd](https://w1.fi/hostapd) - Ứng dụng WiFi AP xuất sắc
- [Flask](https://flask.palletsprojects.com/) - Web framework Python
- [Lucide Icons](https://lucide.dev/) - Bộ icon đẹp mắt
- [psutil](https://github.com/giampaolo/psutil) - Thư viện tiện ích hệ thống đa nền tảng


## 📧 Hỗ trợ

Nếu gặp vấn đề hoặc có câu hỏi:

1. Xem phần [Troubleshooting](#-troubleshooting)
2. Xem qua [existing issues](https://github.com/thanhtantran/opi4pro_wifi6_hotspot/issues)
3. Tạo issue mới với thông tin chi tiết

## 🗺️ Lộ trình

- [ ] Thêm xác thực cho giao diện web
- [ ] Hỗ trợ HTTPS với chứng chỉ SSL
- [ ] Lưu/tải preset cấu hình
- [ ] Giới hạn băng thông theo từng client
- [ ] Tạo QR code để kết nối nhanh
- [ ] Gửi email thông báo sự kiện
- [ ] Hỗ trợ đa ngôn ngữ
- [ ] Docker containerization


## ⭐ Lịch sử Star

Nếu thấy dự án hữu ích, hãy cân nhắc tặng một star!

---

**Làm với ❤️ bởi [Orange Pi Vietnam](https://orangepi.vn)**
