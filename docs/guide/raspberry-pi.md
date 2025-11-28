# Raspberry Pi Deployment

Deploy TAD on Raspberry Pi for portable, low-power mesh networks.

## Requirements

### Hardware
- **Raspberry Pi 3/4/5** or Zero 2 W (minimum)
- **16GB+ SD card** (32GB recommended)
- **Power supply** (official recommended)
- **Network:** Wi-Fi or Ethernet

### Software
- **Raspberry Pi OS** (32-bit or 64-bit)
- **Python 3.8+** (pre-installed on recent images)

## Quick Setup

### 1. Prepare Raspberry Pi

```bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3-pip python3-venv git avahi-daemon

# Enable mDNS
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

### 2. Install TAD

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/tad.git
cd tad

# Run installer
./install.sh

# Start TAD
./tad
```

### 3. Test Installation

```bash
# Check if running
ps aux | grep tad

# Test connectivity from another device
ping raspberrypi.local
```

## Headless Setup

### SSH Installation

```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Install TAD
git clone https://github.com/fabriziosalmi/tad.git
cd tad
./install.sh --service

# Enable service
sudo systemctl enable tad
sudo systemctl start tad

# Check status
sudo systemctl status tad
```

### Auto-Start on Boot

```bash
# Install as system service
sudo ./install.sh --service

# Enable auto-start
sudo systemctl enable tad

# Verify
sudo systemctl is-enabled tad
```

## Wi-Fi Access Point Mode

Turn your Raspberry Pi into a TAD mesh node + Wi-Fi hotspot.

### Install hostapd and dnsmasq

```bash
sudo apt install -y hostapd dnsmasq
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
```

### Configure Static IP

Edit `/etc/dhcpcd.conf`:

```bash
sudo nano /etc/dhcpcd.conf
```

Add:
```
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant
```

### Configure dnsmasq

```bash
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
```

Add:
```
interface=wlan0
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
```

### Configure hostapd

```bash
sudo nano /etc/hostapd/hostapd.conf
```

Add:
```
interface=wlan0
driver=nl80211
ssid=TAD-Mesh
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=YourSecurePassword
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
```

### Enable Services

```bash
sudo systemctl unmask hostapd
sudo systemctl enable hostapd
sudo systemctl start hostapd
sudo systemctl start dnsmasq
```

### Test

```bash
# Check AP is running
sudo systemctl status hostapd

# Connect from device and check
ping 192.168.4.1
```

## Performance Optimization

### Disable Unnecessary Services

```bash
# Disable Bluetooth if not needed
sudo systemctl disable bluetooth

# Disable GUI (if headless)
sudo systemctl set-default multi-user.target

# Disable Wi-Fi power management
sudo iwconfig wlan0 power off
```

### Increase Swap (for Pi Zero/3)

```bash
# Increase swap size
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=1024

sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### SD Card Optimization

```bash
# Reduce writes to SD card
# Use RAM for logs
sudo nano /etc/fstab
```

Add:
```
tmpfs /tmp tmpfs defaults,noatime,nosuid,size=100m 0 0
tmpfs /var/log tmpfs defaults,noatime,nosuid,mode=0755,size=100m 0 0
```

## Power Management

### Auto-Shutdown on Low Battery (with UPS HAT)

```bash
#!/bin/bash
# /usr/local/bin/battery_monitor.sh

BATTERY=$(cat /sys/class/power_supply/BAT0/capacity)

if [ "$BATTERY" -lt 10 ]; then
    # Export data before shutdown
    cd /opt/tad
    echo "/export-all" | sudo -u tad ./tad
    
    # Shutdown
    sudo shutdown -h now
fi
```

Add to crontab:
```bash
*/5 * * * * /usr/local/bin/battery_monitor.sh
```

## Remote Access

### VNC Setup

```bash
# Install VNC
sudo apt install -y realvnc-vnc-server

# Enable VNC
sudo raspi-config
# Interface Options → VNC → Enable
```

### SSH Key Authentication

```bash
# On your computer
ssh-keygen -t ed25519

# Copy to Pi
ssh-copy-id pi@raspberrypi.local

# Disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no

sudo systemctl restart ssh
```

## Multi-Pi Mesh Network

### Setup Multiple Nodes

**Node 1 (Main):**
```bash
# Configure as AP + TAD
hostname: tad-node1
IP: 192.168.4.1
```

**Node 2-N (Clients):**
```bash
# Connect to Node 1's AP
# Run TAD
hostname: tad-node2, tad-node3, etc.
```

### Automatic Peer Discovery

```bash
# Nodes will auto-discover via mDNS
> /peers
Connected peers: 3
- tad-node1: 192.168.4.1
- tad-node2: 192.168.4.2
- tad-node3: 192.168.4.3
```

## Monitoring

### Install Monitoring Tools

```bash
sudo apt install -y htop iotop nethogs

# Monitor CPU/RAM
htop

# Monitor network
sudo nethogs wlan0

# Monitor disk I/O
sudo iotop
```

### Temperature Monitoring

```bash
# Check temperature
vcgencmd measure_temp

# Auto-throttle warning
cat > /usr/local/bin/temp_monitor.sh << 'EOF'
#!/bin/bash
TEMP=$(vcgencmd measure_temp | cut -d= -f2 | cut -d\' -f1)
if (( $(echo "$TEMP > 80" | bc -l) )); then
    echo "High temperature: $TEMP°C" | mail -s "Pi Temperature Alert" admin@example.com
fi
EOF

chmod +x /usr/local/bin/temp_monitor.sh

# Add to crontab
*/5 * * * * /usr/local/bin/temp_monitor.sh
```

## Portable Setup

### Battery Power (with UPS HAT)

```bash
# Monitor battery via GPIO
sudo apt install -y python3-gpiozero

# Battery script
cat > battery_status.py << 'EOF'
from gpiozero import LED
import time

# Assuming battery LED on GPIO 17
battery = LED(17)

while True:
    if battery.is_lit:
        print("Battery OK")
    else:
        print("Low battery - save and shutdown!")
    time.sleep(60)
EOF
```

### Ruggedized Case

Recommended cases for field use:
- **SmartiPi Touch 2** - With touchscreen
- **Argon ONE** - With cooling
- **Pelican-style cases** - Waterproof
- **DIN rail mounts** - Industrial

## Use Cases

### Festival/Event Mesh

```bash
# Setup 5-10 Raspberry Pis as mesh nodes
# Spread across venue
# Auto-discover and form mesh
# Attendees connect and chat

# Benefits:
# - No internet needed
# - Works in crowd
# - Low cost per node
```

### Emergency Communication

```bash
# Solar-powered Pi with UPS
# Weatherproof enclosure
# Mounted at high point
# Acts as relay node

# Provides:
# - Coordination during emergencies
# - Off-grid communication
# - Data collection point
```

### Tactical Deployment

```bash
# Backpack-mounted Pi
# Battery powered
# Creates mobile hotspot
# Bridges between groups

# Features:
# - Portable
# - Quick deployment
# - Extends mesh range
```

## Troubleshooting

### Pi Won't Boot

1. Check power supply (use official)
2. Re-flash SD card
3. Check SD card isn't corrupted
4. Try different SD card

### Wi-Fi Issues

```bash
# Check Wi-Fi status
sudo iwconfig wlan0

# Restart Wi-Fi
sudo ifconfig wlan0 down
sudo ifconfig wlan0 up

# Check country code
sudo raspi-config
# Localisation Options → WLAN Country
```

### Performance Issues

```bash
# Check throttling
vcgencmd get_throttled
# 0x0 = OK
# 0x50000 = Throttled due to undervoltage

# Use better power supply
# Add heatsinks
# Improve ventilation
```

### TAD Won't Start

```bash
# Check logs
sudo journalctl -u tad -n 50

# Test manually
cd /opt/tad
sudo -u tad ./tad

# Check Python version
python3 --version
```

## Advanced Configuration

### Read-Only Filesystem

Protect SD card from corruption:

```bash
# Install overlay package
sudo apt install -y overlayroot

# Enable overlay
sudo nano /etc/overlayroot.conf
# Set: overlayroot="tmpfs"

# Reboot
sudo reboot
```

### Custom LED Indicators

```python
# /opt/tad/led_status.py
from gpiozero import LED
import time

red = LED(17)
green = LED(27)
blue = LED(22)

# Connected = green
# Disconnected = red
# Activity = blue blink
```

## Resources

- [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/)
- [Pi-hole](https://pi-hole.net/) - Network-wide ad blocking (optional)
- [Hostapd Guide](https://www.raspberrypi.org/documentation/configuration/wireless/access-point.md)

## See Also

- [Docker](/guide/docker) - Container deployment
- [Service](/guide/service) - systemd configuration
- [Deployment](/guide/deployment) - General deployment guide
