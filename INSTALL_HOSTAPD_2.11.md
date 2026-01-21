# Hướng Dẫn Cài Đặt hostapd 2.11 từ Source

> Áp dụng cho Orange Pi 4 Pro (AIC8800DC Wi-Fi 6) trên Ubuntu/Debian ARM64  
> Mục tiêu: Kích hoạt **802.11ax (Wi-Fi 6)** trong chế độ AP

---

## 🔧 Các bước thực hiện

### 1. Tải bản release chính thức

```bash
wget https://w1.fi/releases/hostapd-2.11.tar.gz
```

### 2. Giải nén

```bash
tar -xzf hostapd-2.11.tar.gz
```

### 3. Vào thư mục hostapd

```bash
cd hostapd-2.11/hostapd
```

### 4. Sao chép file cấu hình mặc định

> ⚠️ Lưu ý: tên file là `defconfig` (không phải `deconfig`)

```bash
cp defconfig .config
```

### 5. Chỉnh sửa file `.config`

Mở bằng `nano`:

```bash
nano .config
```

Tìm và **bỏ comment (xóa dấu `#`)** hoặc **thêm** các dòng sau:

```ini
CONFIG_IEEE80211N=y
CONFIG_IEEE80211AC=y
CONFIG_IEEE80211AX=y
CONFIG_DRIVER_NL80211=y
CONFIG_LIBNL32=y
```

> 💡 Ghi chú:
> - `CONFIG_IEEE80211AX=y` → bật hỗ trợ **802.11ax (HE)**
> - `CONFIG_IEEE80211AC=y` → bật **802.11ac (VHT)**
> - Không có tùy chọn "be" — có thể bạn nhầm với "HE" (High Efficiency)

Lưu file: `Ctrl+O` → Enter → `Ctrl+X`

### 6. Build

```bash
make -j$(nproc)
```

> ✅ Nếu thành công, file thực thi `hostapd` sẽ nằm trong thư mục hiện tại.

---

## ▶️ Chạy thử

```bash
sudo ./hostapd /etc/hostapd/hostapd.conf
```

> Đảm bảo đã đặt `country_code` trước:
> ```bash
> sudo iw reg set US
> ```

---

## 📄 Ví dụ file `/etc/hostapd/hostapd.conf` hỗ trợ 802.11ax

```ini
interface=wlan0
driver=nl80211
ssid=OrangePi_AX_Test
hw_mode=a
channel=36
country_code=US

ieee80211n=1
ieee80211ac=1
ieee80211ax=1

ht_capab=[HT40+][SHORT-GI-20][SHORT-GI-40]
vht_oper_chwidth=1
vht_oper_centr_freq_seg0_idx=42
he_oper_chwidth=1
he_oper_centr_freq_seg0_idx=42

wpa=2
wpa_passphrase=YourSecurePassword123
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

auth_algs=1
wmm_enabled=1
```

---

## 🔍 Kiểm tra kết quả

Sau khi client kết nối:

```bash
iw wlan0 station dump | grep "bitrate"
```

- `VHT-MCS` → 802.11ac
- `HE-MCS` → 802.11ax

✅ Hoàn tất!