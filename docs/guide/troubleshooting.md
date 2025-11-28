# Troubleshooting

Common issues and solutions for TAD.

## Installation Issues

### Python Version Error

**Problem:** `Python 3.8+ required`

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.8+ (Ubuntu/Debian)
sudo apt update
sudo apt install python3.11

# macOS with Homebrew
brew install python@3.11
```

### Module Not Found

**Problem:** `ModuleNotFoundError: No module named 'xyz'`

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Or force reinstall
pip install --force-reinstall -r requirements.txt
```

### Permission Denied

**Problem:** Cannot execute `install.sh` or `tad`

**Solution:**
```bash
# Make scripts executable
chmod +x install.sh
chmod +x tad

# Run installer
./install.sh
```

## Network Issues

### No Peers Discovered

**Problem:** TAD starts but no peers appear

**Possible Causes:**
1. Devices not on same network
2. Firewall blocking ports
3. mDNS not working
4. Different subnets

**Solutions:**

**1. Verify Network Connectivity**
```bash
# Check you're on same network
ip addr  # Linux
ifconfig  # macOS

# Ping other device
ping <peer-ip>
```

**2. Check Firewall**
```bash
# Linux (UFW)
sudo ufw allow 8765/tcp
sudo ufw allow 8765/udp
sudo ufw allow 5353/udp  # mDNS

# macOS
# System Preferences → Security & Privacy → Firewall → Firewall Options
# Add Python/TAD to allowed apps

# Check if port is listening
sudo lsof -i :8765
netstat -an | grep 8765
```

**3. Test mDNS**
```bash
# Install avahi (Linux)
sudo apt install avahi-daemon avahi-utils
sudo systemctl start avahi-daemon

# Test mDNS discovery
avahi-browse -a

# macOS - should work by default (Bonjour)
dns-sd -B _tad._tcp
```

**4. Manual Peer Connection**
```bash
# If mDNS fails, connect manually
> /connect 192.168.1.100:8765
```

### Port Already in Use

**Problem:** `Address already in use: 8765`

**Solution:**
```bash
# Find process using port
sudo lsof -i :8765
# Or
sudo netstat -tulpn | grep 8765

# Kill process
sudo kill -9 <PID>

# Or use different port
python -m tad.main --port 9000
```

### Intermittent Connectivity

**Problem:** Peers connect and disconnect randomly

**Solutions:**
1. Check Wi-Fi signal strength
2. Disable Wi-Fi power saving
3. Use wired connection
4. Check router settings (AP isolation)

```bash
# Disable Wi-Fi power management (Linux)
sudo iwconfig wlan0 power off

# Check connection stability
ping -c 100 <peer-ip>
```

## Database Issues

### Database Locked

**Problem:** `database is locked`

**Solution:**
```bash
# Close all TAD instances
killall python

# Check for lock file
ls -la tad_data/tad.db*
rm tad_data/tad.db-shm tad_data/tad.db-wal  # If safe

# Restart TAD
./tad
```

### Corrupted Database

**Problem:** Database errors, crashes on startup

**Solution:**
```bash
# Backup first
cp tad_data/tad.db tad_data/tad.db.backup

# Check database integrity
sqlite3 tad_data/tad.db "PRAGMA integrity_check;"

# If corrupted, recover what you can
sqlite3 tad_data/tad.db ".recover" > recovered.sql
sqlite3 tad_data/tad_new.db < recovered.sql

# Or start fresh (LOSES DATA!)
rm tad_data/tad.db
./tad
```

### Database Too Large

**Problem:** Database file very large, slow performance

**Solution:**
```bash
# Check size
du -h tad_data/tad.db

# Vacuum database
sqlite3 tad_data/tad.db "VACUUM;"

# Archive old messages
> /export #general
> /clear #general

# Or use auto-cleanup in config
```

## Channel Issues

### Can't Create Channel

**Problem:** `/create #channel` fails

**Solutions:**
1. Check channel name format (starts with #, alphanumeric)
2. Channel might already exist (`/channels`)
3. Database permissions

```bash
# Valid channel names
/create #general    ✅
/create #dev-team   ✅
/create #room_123   ✅

# Invalid
/create general     ❌ (missing #)
/create #a          ❌ (too short)
/create #my channel ❌ (space)
```

### Messages Not Syncing

**Problem:** Send message but others don't receive

**Solutions:**
```bash
# Check connected peers
> /peers

# Force resync
> /resync

# Check channel info
> /info #general

# Restart TAD
> /quit
./tad
```

### Can't Join Private Channel

**Problem:** `/join-private #channel password` fails

**Solutions:**
1. Verify password is correct (case-sensitive!)
2. Channel might not exist yet
3. Password might have changed

```bash
# Check channel exists
> /channels

# Try creating it first
> /create-private #secret mypassword

# Verify with channel creator
```

## Encryption Issues

### Decryption Failed

**Problem:** Can't decrypt messages in private channel

**Solutions:**
1. Wrong password
2. Encryption key mismatch
3. Corrupted encrypted data

```bash
# Leave and rejoin with correct password
> /leave #private
> /join-private #private correctpassword

# Verify encryption status
> /verify #private
```

### Messages Show as Gibberish

**Problem:** See encrypted text instead of plain text

**Solution:** You haven't joined the private channel properly

```bash
# Join with password
> /join-private #channelname password
```

## Performance Issues

### High CPU Usage

**Problem:** Python process using lots of CPU

**Solutions:**
1. Too many messages/peers
2. Infinite loop bug
3. Large message backlog

```bash
# Check process stats
top | grep python
htop

# Reduce load
> /leave #busy-channel

# Update to latest version
git pull
./install.sh
```

### High Memory Usage

**Problem:** TAD using too much RAM

**Solutions:**
```bash
# Check memory usage
ps aux | grep python

# Clear old messages
> /clear #general
> /export #general  # Backup first

# Restart TAD
> /quit
./tad
```

### Slow Message Delivery

**Problem:** Messages take long to arrive

**Causes:**
1. Network latency
2. Too many peers
3. Large gossip backlog

**Solutions:**
```bash
# Check network latency
ping <peer-ip>

# Reduce gossip load (if available)
> /config gossip.fanout 3

# Limit peers (if configurable)
> /config max_peers 20
```

## UI/Display Issues

### Terminal Colors Wrong

**Problem:** Colors not displaying or showing weird characters

**Solution:**
```bash
# Check terminal supports colors
echo $TERM

# Try different terminal
# - Linux: gnome-terminal, konsole, alacritty
# - macOS: iTerm2, Alacritty

# Disable colors if needed
export TAD_NO_COLOR=1
./tad
```

### Text Garbled/Overlapping

**Problem:** UI elements overlap or display incorrectly

**Solutions:**
1. Resize terminal window
2. Update terminal emulator
3. Try different terminal

```bash
# Minimum recommended size
# 80 columns x 24 rows

# Reset terminal
reset

# Clear screen
clear
# Or in TAD
> /clear-screen
```

### TUI Not Responding

**Problem:** Can't type or navigate UI

**Solutions:**
```bash
# Force quit
Ctrl+C
# Or
kill -9 <pid>

# Check for hung processes
ps aux | grep tad

# Restart
./tad
```

## Export/Import Issues

### Export Fails

**Problem:** `/export` command fails

**Solutions:**
```bash
# Check disk space
df -h

# Check permissions
ls -la exports/
chmod 755 exports/

# Create export directory
mkdir -p exports/

# Try different format
> /export #general txt
```

### Import Fails

**Problem:** Cannot import messages from file

**Solutions:**
```bash
# Verify file exists
ls -la exports/general*.json

# Check file format
file exports/general_20241128.json

# Validate JSON
cat exports/general_20241128.json | python -m json.tool

# Try force import
> /import exports/general_20241128.json --force
```

## Service Issues

### Service Won't Start

**Problem:** `systemctl start tad` fails

**Solutions:**
```bash
# Check service status
sudo systemctl status tad

# View full logs
sudo journalctl -u tad -n 100 --no-pager

# Check service file syntax
sudo systemctl cat tad

# Verify paths in service file
which python3
ls -la /opt/tad/

# Fix permissions
sudo chown -R tad:tad /opt/tad
```

### Service Crashes on Boot

**Problem:** Service starts but immediately crashes

**Solutions:**
```bash
# Check logs
sudo journalctl -u tad -b

# Test manual start
sudo -u tad /opt/tad/venv/bin/python -m tad.main

# Check dependencies
sudo -u tad /opt/tad/venv/bin/pip list

# Increase restart delay
sudo systemctl edit tad
# Add: RestartSec=30
```

## Logging and Debugging

### Enable Debug Logging

```bash
# Run with debug output
python -m tad.main --log-level DEBUG

# Or set environment variable
export TAD_LOG_LEVEL=DEBUG
./tad

# Save to file
python -m tad.main --log-file tad_debug.log
```

### Check Logs

```bash
# System service logs
sudo journalctl -u tad -f

# Application logs (if configured)
tail -f /var/log/tad/tad.log

# Docker logs
docker logs -f tad
```

## Recovery Procedures

### Emergency Backup

```bash
# Quick backup before fixes
cp -r tad_data/ tad_data_backup_$(date +%Y%m%d)

# Export all data
for channel in general dev team; do
    echo "/export #$channel" | python -m tad.main
done
```

### Complete Reset

**⚠️ WARNING: Loses all data!**

```bash
# Backup first!
cp -r tad_data/ tad_data_backup/

# Remove all data
rm -rf tad_data/

# Reinstall
./uninstall.sh
./install.sh

# Start fresh
./tad
```

### Downgrade to Stable

```bash
# Check version
git log --oneline | head

# Backup
cp -r tad_data/ tad_data_backup/

# Checkout stable version
git checkout v1.0  # or specific commit

# Reinstall
./install.sh
```

## Getting Help

### Collect Diagnostic Info

```bash
# Create diagnostic report
cat > tad_diagnostic.txt << EOF
TAD Version: $(git describe --tags)
Python Version: $(python3 --version)
OS: $(uname -a)
Network: $(ip addr)
Processes: $(ps aux | grep tad)
Disk: $(df -h)
Logs: $(tail -50 /var/log/tad/tad.log)
EOF
```

### Report a Bug

Include:
1. TAD version (`git describe --tags`)
2. Python version (`python3 --version`)
3. OS and version
4. Steps to reproduce
5. Error messages/logs
6. Expected vs actual behavior

Submit to: https://github.com/fabriziosalmi/tad/issues

## Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection refused` | Peer offline or firewall | Check network, firewall |
| `Permission denied` | File permissions | Fix with `chmod`, `chown` |
| `Database locked` | Multiple instances | Kill processes, remove lock |
| `Module not found` | Missing dependencies | `pip install -r requirements.txt` |
| `Address in use` | Port conflict | Change port or kill process |
| `No route to host` | Network issue | Check IP, routing, firewall |

## See Also

- [Installation](/guide/installation) - Setup guide
- [Basic Usage](/guide/basic-usage) - How to use TAD
- [Deployment](/guide/deployment) - Production setup
- [GitHub Issues](https://github.com/fabriziosalmi/tad/issues) - Report bugs
