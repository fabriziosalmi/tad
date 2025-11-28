# Running as Service

Configure TAD to run as a system service on Linux and macOS.

## Linux (systemd)

### Installation

TAD includes a systemd service file. Install with:

```bash
sudo ./install.sh --service
```

Or manually:

```bash
# Copy service file
sudo cp tad.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable tad

# Start service
sudo systemctl start tad
```

### Service File

`/etc/systemd/system/tad.service`:

```ini
[Unit]
Description=TAD - Tactical Autonomous Zone Communications
After=network.target

[Service]
Type=simple
User=tad
Group=tad
WorkingDirectory=/opt/tad
ExecStart=/opt/tad/venv/bin/python -m tad.main
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/tad/data

[Install]
WantedBy=multi-user.target
```

### Managing the Service

```bash
# Start TAD
sudo systemctl start tad

# Stop TAD
sudo systemctl stop tad

# Restart TAD
sudo systemctl restart tad

# Check status
sudo systemctl status tad

# View logs
sudo journalctl -u tad -f

# Enable auto-start on boot
sudo systemctl enable tad

# Disable auto-start
sudo systemctl disable tad
```

### Creating Service User

For better security, run as dedicated user:

```bash
# Create user
sudo useradd -r -s /bin/false -d /opt/tad tad

# Create directories
sudo mkdir -p /opt/tad/data
sudo chown -R tad:tad /opt/tad

# Install TAD
sudo -u tad git clone https://github.com/fabriziosalmi/tad.git /opt/tad
cd /opt/tad
sudo -u tad ./install.sh
```

## macOS (launchd)

### Launch Agent

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
        <string>/Users/YOUR_USERNAME/tad/venv/bin/python</string>
        <string>-m</string>
        <string>tad.main</string>
    </array>
    
    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/tad</string>
    
    <key>RunAtLoad</key>
    <true/>
    
    <key>KeepAlive</key>
    <true/>
    
    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/tad/logs/stdout.log</string>
    
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/tad/logs/stderr.log</string>
</dict>
</plist>
```

### Managing Launch Agent

```bash
# Load service
launchctl load ~/Library/LaunchAgents/com.tad.plist

# Unload service
launchctl unload ~/Library/LaunchAgents/com.tad.plist

# Start service
launchctl start com.tad

# Stop service
launchctl stop com.tad

# Check status
launchctl list | grep tad

# View logs
tail -f ~/tad/logs/stdout.log
```

## Docker

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  tad:
    build: .
    container_name: tad
    restart: unless-stopped
    network_mode: host
    volumes:
      - ./data:/app/data
      - ./exports:/app/exports
    environment:
      - TAD_PORT=8765
      - TAD_AUTO_DISCOVER=true
```

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY tad/ ./tad/
COPY tad.py .

VOLUME ["/app/data", "/app/exports"]

EXPOSE 8765/udp
EXPOSE 8765/tcp

CMD ["python", "-m", "tad.main"]
```

### Running with Docker

```bash
# Build image
docker-compose build

# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down

# Restart
docker-compose restart
```

## Process Management (Alternative)

### Using screen

```bash
# Start in screen session
screen -S tad -dm python -m tad.main

# Attach to session
screen -r tad

# Detach: Ctrl+A, D

# Kill session
screen -X -S tad quit
```

### Using tmux

```bash
# Start in tmux session
tmux new-session -d -s tad 'python -m tad.main'

# Attach to session
tmux attach -t tad

# Detach: Ctrl+B, D

# Kill session
tmux kill-session -t tad
```

### Using supervisor

Install supervisor:
```bash
sudo apt install supervisor  # Ubuntu/Debian
sudo yum install supervisor  # CentOS/RHEL
```

Create `/etc/supervisor/conf.d/tad.conf`:
```ini
[program:tad]
command=/opt/tad/venv/bin/python -m tad.main
directory=/opt/tad
user=tad
autostart=true
autorestart=true
stderr_logfile=/var/log/tad/stderr.log
stdout_logfile=/var/log/tad/stdout.log
```

Manage:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start tad
sudo supervisorctl status tad
```

## Auto-Start Configuration

### Environment Variables

Create `/opt/tad/.env`:
```bash
TAD_PORT=8765
TAD_DISCOVERY=true
TAD_AUTO_JOIN=general,dev
TAD_LOG_LEVEL=INFO
```

Update service to load env:
```ini
[Service]
EnvironmentFile=/opt/tad/.env
```

### Configuration File

Create `/opt/tad/config.yaml`:
```yaml
network:
  port: 8765
  discovery: true
  
channels:
  auto_join:
    - general
    - dev
    
logging:
  level: INFO
  file: /var/log/tad/tad.log
```

## Monitoring

### Health Checks

Create health check script:
```bash
#!/bin/bash
# /usr/local/bin/tad_health_check.sh

STATUS=$(systemctl is-active tad)

if [ "$STATUS" != "active" ]; then
    echo "TAD is not running. Attempting restart..."
    systemctl start tad
    
    # Send alert
    echo "TAD restarted at $(date)" | mail -s "TAD Service Alert" admin@example.com
fi
```

Add to crontab:
```bash
*/5 * * * * /usr/local/bin/tad_health_check.sh
```

### Log Rotation

Create `/etc/logrotate.d/tad`:
```
/var/log/tad/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 tad tad
    sharedscripts
    postrotate
        systemctl reload tad > /dev/null 2>&1 || true
    endscript
}
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status tad

# View recent logs
sudo journalctl -u tad -n 50

# Check configuration
sudo systemctl cat tad

# Verify executable
sudo -u tad /opt/tad/venv/bin/python -m tad.main
```

### Permission Issues

```bash
# Fix ownership
sudo chown -R tad:tad /opt/tad

# Fix permissions
sudo chmod -R 755 /opt/tad
sudo chmod 640 /opt/tad/.env
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8765

# Kill process
sudo kill -9 <PID>

# Or change port in config
```

## See Also

- [Deployment](/guide/deployment) - System-wide installation
- [Docker Guide](/guide/docker) - Container deployment
- [Troubleshooting](/guide/troubleshooting) - Common issues
