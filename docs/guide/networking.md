# Network Configuration

Advanced network configuration and optimization for TAD.

## Network Topology

TAD supports various network configurations:

### 1. Flat Local Network (Default)
All nodes on same subnet, automatic discovery via mDNS.

```
[Node A] ---- [Switch] ---- [Node B]
                 |
              [Node C]
```

### 2. Multi-Subnet with Manual Peering
Nodes on different subnets, manual connection required.

```
[Subnet A]          [Subnet B]
  Node A  <-------->  Node B
  Node C              Node D
```

### 3. Mesh Network
Multiple interconnected nodes creating redundant paths.

```
[Node A] ----- [Node B]
   |    \    /    |
   |     \  /     |
[Node C] -X- [Node D]
   |    /  \     |
   |   /    \    |
[Node E] ----- [Node F]
```

## Discovery Configuration

### mDNS Discovery (Default)

```bash
# Enable automatic discovery
python -m tad.main --discovery

# Disable discovery
python -m tad.main --no-discovery
```

### Custom Discovery Settings

```yaml
# config.yaml
discovery:
  enabled: true
  service_name: "_tad._tcp"
  port: 5353
  announce_interval: 30  # seconds
  ttl: 120              # seconds
```

### Manual Peer Configuration

```bash
# Connect to specific peer
> /connect 192.168.1.100:8765

# Add persistent peer
echo "192.168.1.100:8765" >> peers.txt
python -m tad.main --peers peers.txt
```

## Port Configuration

### Default Ports

- **8765/tcp** - TAD communication
- **8765/udp** - TAD discovery/gossip
- **5353/udp** - mDNS service discovery

### Custom Port

```bash
# Use different port
python -m tad.main --port 9000

# Bind to specific address
python -m tad.main --host 192.168.1.100 --port 8765

# Listen on all interfaces
python -m tad.main --host 0.0.0.0 --port 8765
```

### Multiple Instances

Run multiple TAD instances on same machine:

```bash
# Instance 1
python -m tad.main --port 8765 --data-dir ~/.tad/node1

# Instance 2
python -m tad.main --port 8766 --data-dir ~/.tad/node2

# Instance 3
python -m tad.main --port 8767 --data-dir ~/.tad/node3
```

## Firewall Configuration

### Linux (UFW)

```bash
# Allow TAD ports
sudo ufw allow 8765/tcp
sudo ufw allow 8765/udp
sudo ufw allow 5353/udp

# Limit to local network
sudo ufw allow from 192.168.1.0/24 to any port 8765

# Enable firewall
sudo ufw enable
```

### Linux (iptables)

```bash
# Allow TAD
sudo iptables -A INPUT -p tcp --dport 8765 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 8765 -j ACCEPT
sudo iptables -A INPUT -p udp --dport 5353 -j ACCEPT

# Save rules
sudo iptables-save > /etc/iptables/rules.v4
```

### macOS

```bash
# Add to /etc/pf.conf
pass in proto tcp to port 8765
pass in proto udp to port 8765
pass in proto udp to port 5353

# Reload
sudo pfctl -f /etc/pf.conf
```

### Windows

```powershell
# Allow inbound
netsh advfirewall firewall add rule name="TAD TCP" dir=in action=allow protocol=TCP localport=8765
netsh advfirewall firewall add rule name="TAD UDP" dir=in action=allow protocol=UDP localport=8765
netsh advfirewall firewall add rule name="mDNS" dir=in action=allow protocol=UDP localport=5353
```

## Network Interfaces

### Bind to Specific Interface

```bash
# List interfaces
ip addr  # Linux
ifconfig # macOS

# Bind to interface
python -m tad.main --interface wlan0

# Or by IP
python -m tad.main --host 192.168.1.100
```

### Multi-Interface Setup

```yaml
# config.yaml
network:
  interfaces:
    - name: eth0
      ip: 192.168.1.100
      port: 8765
    - name: wlan0
      ip: 10.0.0.100
      port: 8766
```

## NAT Traversal

### Port Forwarding

For nodes behind NAT:

```bash
# Router configuration
External: <router-ip>:8765 → Internal: 192.168.1.100:8765

# Advertise external address
python -m tad.main --external-ip <router-ip>:8765
```

### UPnP (if supported)

```bash
# Enable UPnP
python -m tad.main --upnp
```

## VPN Integration

### WireGuard

```bash
# Install WireGuard
sudo apt install wireguard

# Configure
sudo nano /etc/wireguard/wg0.conf
```

```ini
[Interface]
PrivateKey = <your-private-key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <peer-public-key>
AllowedIPs = 10.0.0.2/32
Endpoint = <peer-ip>:51820
```

```bash
# Start VPN
sudo wg-quick up wg0

# Bind TAD to VPN interface
python -m tad.main --interface wg0 --host 10.0.0.1
```

### OpenVPN

```bash
# Connect to VPN
sudo openvpn --config client.ovpn

# Find VPN interface
ip addr | grep tun

# Use VPN interface
python -m tad.main --interface tun0
```

## Network Optimization

### TCP Tuning

```bash
# Linux kernel tuning
sudo sysctl -w net.core.rmem_max=16777216
sudo sysctl -w net.core.wmem_max=16777216
sudo sysctl -w net.ipv4.tcp_rmem="4096 87380 16777216"
sudo sysctl -w net.ipv4.tcp_wmem="4096 65536 16777216"

# Make permanent
sudo nano /etc/sysctl.conf
```

### UDP Buffer Sizes

```bash
# Increase UDP buffers
sudo sysctl -w net.core.rmem_default=262144
sudo sysctl -w net.core.wmem_default=262144
```

### Connection Limits

```yaml
# config.yaml
network:
  max_connections: 100
  connection_timeout: 30
  keepalive_interval: 10
  max_message_size: 65536
```

## Quality of Service (QoS)

### Traffic Prioritization

```bash
# Linux tc (Traffic Control)
sudo tc qdisc add dev eth0 root handle 1: htb default 30
sudo tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit

# High priority for TAD
sudo tc class add dev eth0 parent 1:1 classid 1:10 htb rate 50mbit
sudo tc filter add dev eth0 protocol ip parent 1:0 prio 1 u32 match ip dport 8765 0xffff flowid 1:10
```

## Monitoring

### Network Statistics

```bash
# Real-time connections
> /netstat

# Bandwidth usage
> /bandwidth

# Peer latency
> /ping-all
```

### External Tools

```bash
# Monitor TAD traffic
sudo tcpdump -i wlan0 port 8765

# Check connections
netstat -an | grep 8765
ss -tuln | grep 8765

# Bandwidth monitoring
sudo iftop -i wlan0
sudo nethogs wlan0
```

## Troubleshooting

### Check Connectivity

```bash
# Test port open
nc -zv 192.168.1.100 8765

# Test from peer
telnet 192.168.1.100 8765

# Check listening
sudo lsof -i :8765
sudo netstat -tulpn | grep 8765
```

### Debug Discovery

```bash
# Watch mDNS traffic
sudo tcpdump -i wlan0 port 5353 -vv

# Test mDNS resolution
avahi-browse -a
dns-sd -B _tad._tcp
```

### Network Path Testing

```bash
# Trace route to peer
traceroute 192.168.1.100

# MTU discovery
ping -M do -s 1472 192.168.1.100

# Packet loss test
ping -c 100 192.168.1.100 | grep loss
```

## Advanced Topics

### IPv6 Support

```bash
# Enable IPv6
python -m tad.main --ipv6

# Bind to IPv6 address
python -m tad.main --host ::1 --port 8765
```

### Multicast Configuration

```bash
# Set multicast interface
python -m tad.main --multicast-interface wlan0

# Configure multicast TTL
python -m tad.main --multicast-ttl 32
```

### Custom Protocol

```yaml
# config.yaml
protocol:
  version: "1.0"
  encryption: "tls"
  compression: "gzip"
  custom_headers:
    User-Agent: "TAD/1.0"
```

## Performance Tuning

### Gossip Protocol

```yaml
# config.yaml
gossip:
  fanout: 3           # Peers to forward to
  interval: 1.0       # Gossip interval (seconds)
  ttl: 5              # Message TTL (hops)
  cache_size: 10000   # Seen messages cache
```

### Connection Pooling

```yaml
# config.yaml
connection_pool:
  size: 50
  timeout: 300
  max_lifetime: 3600
  reuse: true
```

## See Also

- [Installation](/guide/installation) - Setup guide
- [Deployment](/guide/deployment) - Production deployment
- [Troubleshooting](/guide/troubleshooting) - Common issues
- [Architecture](/reference/architecture) - Network design
