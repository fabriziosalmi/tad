# Security Hardening

Best practices for securing your TAD installation.

## Threat Model

### What TAD Protects Against

✅ **Network eavesdropping** (private channels with E2E encryption)  
✅ **Unauthorized message viewing** (encrypted storage)  
✅ **Message tampering** (cryptographic signatures)  
✅ **Impersonation** (public key infrastructure)

### What TAD Does NOT Protect Against

❌ **Compromised endpoints** - If device is hacked, messages visible  
❌ **Malicious peers** - Can spam or attempt DoS  
❌ **Traffic analysis** - Network observers see metadata  
❌ **Physical access** - Direct database access bypasses encryption  
❌ **Social engineering** - User shares passwords/keys

## Network Security

### Firewall Configuration

#### Minimal Access (Recommended)

```bash
# Allow only TAD ports
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 8765/tcp comment 'TAD'
sudo ufw allow 8765/udp comment 'TAD'
sudo ufw allow 5353/udp comment 'mDNS'
sudo ufw enable
```

#### Local Network Only

```bash
# Restrict to local network
sudo ufw allow from 192.168.1.0/24 to any port 8765 proto tcp
sudo ufw allow from 192.168.1.0/24 to any port 8765 proto udp
```

#### Strict Mode (VPN/Trusted Network)

```bash
# Only allow specific IPs
sudo ufw allow from 192.168.1.100 to any port 8765
sudo ufw allow from 192.168.1.101 to any port 8765
```

### Network Isolation

#### Use Separate Network Interface

```bash
# Bind to specific interface
python -m tad.main --interface wlan1

# Check interfaces
ip addr show
```

#### VPN Tunnel

```bash
# Route TAD over VPN
# 1. Setup WireGuard/OpenVPN
# 2. Bind TAD to VPN interface
python -m tad.main --interface wg0
```

### Disable Public Discovery

```bash
# Disable mDNS discovery
python -m tad.main --no-discovery

# Manual peer connections only
> /connect 192.168.1.100:8765
```

## Encryption

### Private Channels Best Practices

#### Strong Passwords

```bash
# Generate strong password
openssl rand -base64 32

# Use passphrase
/create-private #secure "correct horse battery staple magnificent"

# Avoid weak passwords
❌ password123
❌ admin
❌ secret
✅ Use password manager
✅ 20+ characters
✅ Random generation
```

#### Key Derivation Settings

Increase PBKDF2 iterations (requires code modification):

```python
# In tad/crypto/e2ee.py
PBKDF2_ITERATIONS = 500000  # Increase from default 100000
```

#### Password Rotation

```bash
# Rotate channel passwords quarterly
> /rekey #sensitive oldpassword newpassword

# Document rotation schedule
# - High security: Weekly
# - Normal: Monthly  
# - Low: Quarterly
```

### Database Encryption

#### Encrypt Database at Rest

```bash
# Using LUKS (Linux)
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup open /dev/sdb1 tad_encrypted
sudo mkfs.ext4 /dev/mapper/tad_encrypted
sudo mount /dev/mapper/tad_encrypted /opt/tad/data

# Or use eCryptfs
sudo mount -t ecryptfs /opt/tad/data /opt/tad/data
```

#### Encrypted Backup

```bash
# Encrypt exports with GPG
> /export #general
gpg --symmetric --cipher-algo AES256 exports/general_*.json

# Decrypt when needed
gpg --decrypt exports/general_*.json.gpg > general.json
```

### Secure Key Storage

```bash
# Restrict permissions on identity files
chmod 600 tad_data/identity.key
chmod 600 tad_data/*.pem

# Store keys in secure location
mkdir -p ~/.tad/keys
chmod 700 ~/.tad/keys
mv tad_data/*.key ~/.tad/keys/
```

## Access Control

### File Permissions

```bash
# Secure TAD installation
sudo chown -R tad:tad /opt/tad
sudo chmod 750 /opt/tad
sudo chmod 700 /opt/tad/data
sudo chmod 600 /opt/tad/data/*
sudo chmod 640 /opt/tad/config.yaml
```

### User Isolation

```bash
# Run as dedicated user (not root!)
sudo useradd -r -s /bin/false tad
sudo -u tad python -m tad.main

# Verify not running as root
ps aux | grep tad | grep -v root
```

### SELinux/AppArmor

#### SELinux Policy (RHEL/CentOS)

```bash
# Create policy
cat > tad.te << EOF
module tad 1.0;
require {
    type user_t;
    type user_home_t;
    class tcp_socket { bind listen };
}
allow user_t user_home_t:tcp_socket { bind listen };
EOF

# Compile and load
checkmodule -M -m -o tad.mod tad.te
semodule_package -o tad.pp -m tad.mod
sudo semodule -i tad.pp
```

#### AppArmor Profile (Ubuntu/Debian)

```bash
# Create profile
sudo cat > /etc/apparmor.d/tad << EOF
#include <tunables/global>

/opt/tad/venv/bin/python {
    #include <abstractions/base>
    #include <abstractions/python>
    
    /opt/tad/** r,
    /opt/tad/data/** rw,
    
    network inet stream,
    network inet dgram,
}
EOF

# Load profile
sudo apparmor_parser -r /etc/apparmor.d/tad
```

## Peer Authentication

### Blocklist Management

```bash
# Block malicious peers
> /kick peer_abc123

# Persist blocklist
echo "peer_abc123" >> tad_data/blocklist.txt

# Auto-load on start
python -m tad.main --blocklist tad_data/blocklist.txt
```

### Allowlist Mode

```bash
# Only allow known peers
> /allowlist-enable
> /allow peer_def456
> /allow peer_ghi789

# Reject all others automatically
```

### Peer Verification

```bash
# Verify peer fingerprint
> /verify-peer peer_abc123
Public Key: AbCdEf...
Fingerprint: SHA256:ab:cd:ef:...

# Compare out-of-band (phone, in-person)
```

## Monitoring and Auditing

### Logging

```bash
# Enable security logging
python -m tad.main --audit-log /var/log/tad/audit.log

# Monitor in real-time
tail -f /var/log/tad/audit.log | grep -E "(WARN|ERROR|SECURITY)"
```

### Intrusion Detection

```bash
# Monitor for suspicious activity
> /audit-log

# Look for:
# - Repeated failed authentications
# - Unknown peer connections
# - Unusual message patterns
# - Database tampering attempts
```

### Alerting

```bash
#!/bin/bash
# tad_security_monitor.sh

LOG_FILE="/var/log/tad/audit.log"
ALERT_EMAIL="admin@example.com"

# Monitor for security events
tail -Fn0 "$LOG_FILE" | while read line; do
    if echo "$line" | grep -qE "(SECURITY|ATTACK|BREACH)"; then
        echo "$line" | mail -s "TAD Security Alert" "$ALERT_EMAIL"
    fi
done
```

## Secure Configuration

### Minimal Attack Surface

```yaml
# config.yaml
network:
  port: 8765
  bind: "127.0.0.1"  # Localhost only
  discovery: false    # Disable auto-discovery
  
security:
  require_encryption: true
  allow_public_channels: false
  max_message_size: 4096
  rate_limit: 10  # messages per second
  
audit:
  enabled: true
  log_all_messages: true
  log_connections: true
```

### Disable Dangerous Features

```python
# In config
DISABLE_FEATURES = [
    'auto_update',
    'remote_admin',
    'debug_mode',
    'telemetry'
]
```

## Secure Deployment

### systemd Hardening

```ini
[Service]
# Security features
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/tad/data
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictRealtime=yes
RestrictNamespaces=yes
LockPersonality=yes
MemoryDenyWriteExecute=yes
RestrictAddressFamilies=AF_INET AF_INET6
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM

# Resource limits
LimitNOFILE=1024
LimitNPROC=64
```

### Docker Security

```yaml
# docker-compose.yml
services:
  tad:
    image: tad:latest
    read_only: true
    security_opt:
      - no-new-privileges:true
      - seccomp:unconfined
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    tmpfs:
      - /tmp
    volumes:
      - tad-data:/app/data:rw
```

## Incident Response

### Suspected Breach

```bash
# 1. Isolate
sudo systemctl stop tad
sudo ufw deny 8765

# 2. Preserve evidence
cp -r tad_data/ incident_$(date +%Y%m%d)/
tar czf logs_$(date +%Y%m%d).tar.gz /var/log/tad/

# 3. Analyze
grep -i "security\|error\|warn" /var/log/tad/*.log

# 4. Rotate keys
> /generate-new-identity
> /rekey-all-channels

# 5. Review access
> /audit-log
> /list-peers
```

### Key Compromise

```bash
# Emergency key rotation
> /emergency-rekey

# Notify all users
> /broadcast SECURITY ALERT: Rotating encryption keys

# Document incident
echo "$(date): Key compromise - rotated all keys" >> security_incidents.log
```

## Security Checklist

### Installation
- [ ] Running as non-root user
- [ ] Firewall configured
- [ ] Strong passwords for private channels
- [ ] Database encrypted at rest
- [ ] File permissions restricted (600/700)

### Network
- [ ] mDNS disabled (if not needed)
- [ ] Bound to specific interface
- [ ] VPN configured (if needed)
- [ ] Peer allowlist enabled (if applicable)

### Monitoring
- [ ] Audit logging enabled
- [ ] Log rotation configured
- [ ] Alerts configured
- [ ] Regular log review scheduled

### Maintenance
- [ ] Regular updates applied
- [ ] Backups encrypted
- [ ] Password rotation schedule
- [ ] Incident response plan documented

## Security Updates

```bash
# Check for security updates
git fetch
git log HEAD..origin/main --grep="security"

# Update safely
git pull
./install.sh
sudo systemctl restart tad
```

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

Contact: security@tad-project.org

Include:
- Vulnerability description
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

## Further Reading

- [Private Channels](/guide/private-channels) - Encryption details
- [Deployment](/guide/deployment) - Secure installation
- [Architecture](/reference/architecture) - Security design
- OWASP Cheat Sheets - General security

## Security Disclaimer

TAD is provided "as is" without warranty. Use in high-risk environments requires professional security audit. The developers are not responsible for security breaches or data loss.
