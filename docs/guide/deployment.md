# TAD Deployment Guide

This guide covers different deployment scenarios for TAD.

---

## Table of Contents

1. [Quick Install (Single User)](#quick-install-single-user)
2. [System-Wide Install (Multi-User)](#system-wide-install-multi-user)
3. [Running as Service](#running-as-service)
4. [Docker Deployment](#docker-deployment)
5. [Raspberry Pi](#raspberry-pi)
6. [Network Configuration](#network-configuration)
7. [Security Hardening](#security-hardening)

---

## Quick Install (Single User)

For personal use on your own machine.

```bash
# 1. Clone repository
git clone https://github.com/yourusername/tad.git
cd tad

# 2. Run automatic installer
chmod +x install.sh
./install.sh

# 3. Start TAD
./tad
```

**Pros:**
- ✅ Simple, no root required
- ✅ Isolated in your home directory
- ✅ Easy to update/remove

**Cons:**
- ❌ Only runs when you're logged in
- ❌ Not available to other users

---

## System-Wide Install (Multi-User)

For shared machines where multiple users need TAD.

```bash
# 1. Install to /opt (as root)
sudo git clone https://github.com/yourusername/tad.git /opt/tad
cd /opt/tad

# 2. Create dedicated user
sudo useradd -r -s /bin/false -d /opt/tad tad

# 3. Run installer
sudo ./install.sh

# 4. Set permissions
sudo chown -R tad:tad /opt/tad
sudo chmod 755 /opt/tad

# 5. Create symlink for global access
sudo ln -s /opt/tad/tad /usr/local/bin/tad

# 6. Users can now run
tad
```

**Pros:**
- ✅ Available to all users
- ✅ Centralized updates
- ✅ Standard Linux location

**Cons:**
- ❌ Requires root for installation
- ❌ More complex permissions

---

## Running as Service

For always-on deployments (servers, routers, etc.).

### Automatic (Linux)

```bash
# Use installer with systemd option
./install.sh
# Select "yes" when asked about systemd service
```

### Manual (Linux)

```bash
# 1. Install TAD to /opt
sudo cp -r tad /opt/tad
cd /opt/tad
./install.sh

# 2. Copy service file
sudo cp tad.service /etc/systemd/system/

# 3. Edit service file (adjust paths)
sudo nano /etc/systemd/system/tad.service

# 4. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable tad
sudo systemctl start tad

# 5. Check status
sudo systemctl status tad

# 6. View logs
sudo journalctl -u tad -f
```

### macOS (launchd)

Create `~/Library/LaunchAgents/com.tad.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.tad</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/youruser/tad/venv/bin/python</string>
        <string>-m</string>
        <string>tad.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/youruser/tad</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/tad.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/tad.error.log</string>
</dict>
</plist>
```

Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.tad.plist
launchctl start com.tad
```

---

## Docker Deployment

**Note:** Docker networking can complicate mDNS discovery. Use host networking mode.

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libsodium-dev \
    avahi-daemon \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY tad/ ./tad/
COPY profile.json tad_node.db ./

# Create data volume
VOLUME /app/data

# Expose ports (adjust as needed)
EXPOSE 50000-51000/tcp
EXPOSE 5353/udp

# Run TAD
CMD ["python", "-m", "tad.main"]
```

### Build and Run

```bash
# Build image
docker build -t tad:latest .

# Run with host networking (required for mDNS)
docker run -d \
  --name tad \
  --network host \
  --restart unless-stopped \
  -v tad_data:/app/data \
  tad:latest

# View logs
docker logs -f tad

# Stop
docker stop tad

# Remove
docker rm tad
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tad:
    build: .
    container_name: tad
    network_mode: host
    restart: unless-stopped
    volumes:
      - tad_data:/app/data
    environment:
      - PYTHONUNBUFFERED=1

volumes:
  tad_data:
```

Run:
```bash
docker-compose up -d
```

---

## Raspberry Pi

Perfect for always-on mesh network nodes.

### Requirements
- Raspberry Pi 3/4/5 or Zero W
- Raspbian OS (64-bit recommended)
- 512MB+ RAM

### Installation

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    build-essential \
    libsodium-dev \
    git

# 3. Clone TAD
cd ~
git clone https://github.com/yourusername/tad.git
cd tad

# 4. Run installer
./install.sh

# 5. Install as service (recommended)
# When prompted, select "yes" for systemd service

# 6. Enable on boot
sudo systemctl enable tad
```

### Optimize for Low Power

Edit `/etc/systemd/system/tad.service`:

```ini
# Add to [Service] section
CPUQuota=25%        # Limit to 25% CPU
MemoryMax=128M      # Limit to 128MB RAM
Nice=10             # Lower priority
```

Reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart tad
```

---

## Network Configuration

### Firewall Rules

#### Linux (ufw)

```bash
# Allow mDNS discovery
sudo ufw allow 5353/udp

# Allow TAD connections (adjust port range)
sudo ufw allow 50000:51000/tcp
```

#### Linux (iptables)

```bash
# mDNS
sudo iptables -A INPUT -p udp --dport 5353 -j ACCEPT

# TAD
sudo iptables -A INPUT -p tcp --dport 50000:51000 -j ACCEPT

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

#### macOS

```bash
# macOS firewall allows local network by default
# If using application firewall, add exception:
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --add $(which python3)
```

### Router Configuration

For multi-subnet deployments:

1. **Enable mDNS Reflector**
   - Most routers: Advanced → Services → mDNS/Bonjour
   - OpenWrt: `opkg install avahi-daemon`
   - pfSense: Services → Avahi

2. **Port Forwarding** (if needed)
   - Forward ports 50000-51000 TCP
   - Not needed for same-subnet nodes

---

## Security Hardening

### 1. File Permissions

```bash
# Protect private keys
chmod 600 profile.json
chmod 700 tad_node.db

# Make scripts executable only
chmod 755 install.sh uninstall.sh tad
```

### 2. SELinux (RHEL/Fedora)

```bash
# Allow TAD to bind ports
sudo semanage port -a -t http_port_t -p tcp 50000-51000

# If running as service
sudo setsebool -P httpd_can_network_connect 1
```

### 3. AppArmor (Ubuntu)

Create `/etc/apparmor.d/usr.bin.tad`:

```
#include <tunables/global>

/opt/tad/venv/bin/python {
  #include <abstractions/base>
  #include <abstractions/python>

  /opt/tad/** r,
  /opt/tad/tad_node.db rw,
  /opt/tad/profile.json r,

  network inet stream,
  network inet dgram,
}
```

Load profile:
```bash
sudo apparmor_parser -r /etc/apparmor.d/usr.bin.tad
```

### 4. Minimal Privileges

Run as dedicated user (not root):

```bash
# Create user
sudo useradd -r -s /bin/false tad

# Set ownership
sudo chown -R tad:tad /opt/tad

# Run as tad user
sudo -u tad /opt/tad/tad
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u tad -n 50

# Check service status
sudo systemctl status tad

# Test manually
sudo -u tad /opt/tad/venv/bin/python -m tad.main
```

### Nodes Not Discovering

```bash
# Check mDNS service
sudo systemctl status avahi-daemon  # Linux
dns-sd -B _tad._tcp              # macOS

# Check firewall
sudo ufw status
sudo iptables -L

# Test connectivity
ping <other-node-ip>
```

### High Resource Usage

```bash
# Monitor resources
htop
systemctl status tad

# Limit resources (systemd)
sudo systemctl edit tad
# Add:
# [Service]
# MemoryMax=256M
# CPUQuota=50%
```

---

## Updating TAD

### Standard Install

```bash
cd tad
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### Service Install

```bash
sudo systemctl stop tad
cd /opt/tad
sudo git pull
sudo -u tad ./venv/bin/pip install -r requirements.txt --upgrade
sudo systemctl start tad
```

---

## Backup & Restore

### Backup

```bash
# Essential files
tar -czf tad_backup.tar.gz \
    profile.json \
    tad_node.db

# Or use export command
./tad
> /export
```

### Restore

```bash
# Extract backup
tar -xzf tad_backup.tar.gz

# Or use import command
./tad
> /import backup.json
```

---

## Performance Tuning

### Database Optimization

```bash
# Vacuum database periodically
sqlite3 tad_node.db "VACUUM;"

# Analyze for query optimization
sqlite3 tad_node.db "ANALYZE;"
```

### Python Optimization

```bash
# Run with optimizations
python -O -m tad.main

# Or in systemd service
ExecStart=/opt/tad/venv/bin/python -O -m tad.main
```

---

**Need Help?** See USER_GUIDE.md or open an issue on GitHub.
