# Getting Started

Welcome to TAD! This guide will help you get up and running in minutes.

## What is TAD?

TAD (Tactical Autonomous Zone Communications) is a **peer-to-peer, decentralized chat system** designed for offline-first communication. It works on local networks without internet access and provides end-to-end encrypted private channels.

### Perfect For

- 🎉 **Free Parties** - Coordinate without cell service
- 🏕️ **TAZ (Temporary Autonomous Zones)** - Community self-organization  
- 📢 **Protests & Demonstrations** - Resilient communication
- 🌄 **Remote Locations** - Chat on local networks
- 🔒 **Private Groups** - End-to-end encrypted conversations

## Quick Install

### Automatic Installation (Recommended)

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/tad.git
cd tad

# Run installer
./install.sh

# Start TAD
./tad
```

The installer will:
- ✅ Check Python version (3.8+)
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Run test suite
- ✅ Optionally install systemd service

### Manual Installation

```bash
# Clone repository
git clone https://github.com/fabriziosalmi/tad.git
cd tad

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run TAD
python -m tad.main
```

## First Run

When you start TAD for the first time:

1. **Identity Generation** - Cryptographic keys are created automatically
2. **Database Creation** - SQLite database initialized  
3. **Discovery Starts** - mDNS service begins broadcasting
4. **TUI Opens** - Terminal interface appears

```
┌─────────────────────────────────────────────────┐
│                 TAD v1.0                     │
├──────────┬────────────────────────┬─────────────┤
│          │                        │             │
│ Channels │    Message History     │   Peers     │
│          │                        │             │
│ #general │ [System] Welcome!      │ 👤 (You)    │
│          │                        │             │
│          │                        │             │
│          │                        │             │
├──────────┴────────────────────────┴─────────────┤
│ > Type /help for commands                       │
└─────────────────────────────────────────────────┘
```

## Your First Message

1. **Check peers:**
   ```
   > /peers
   Connected peers: 2
   ```

2. **Send a message:**
   ```
   > Hello, world!
   ```

3. **Create a channel:**
   ```
   > /create #dev
   [SYSTEM] Created channel #dev
   ```

4. **Switch channels:**
   ```
   > /switch #dev
   [SYSTEM] Switched to #dev
   ```

## Next Steps

- 📖 Read the [User Guide](/guide/user-guide) for all commands
- 🔒 Learn about [Private Channels](/guide/private-channels)
- 🚀 See [Deployment](/guide/deployment) for production setups
- 🏗️ Explore the [Architecture](/reference/architecture)

## Requirements

- **Python:** 3.8 or higher
- **OS:** Linux, macOS, Windows (WSL recommended)
- **Network:** Wi-Fi or Ethernet (same local network)
- **Dependencies:** Listed in `requirements.txt`

## Troubleshooting

### Nodes Not Discovering

**Problem:** Started TAD but no peers appear.

**Solutions:**
1. Ensure devices on same network
2. Check firewall allows UDP 5353 (mDNS)
3. Verify Python 3.8+
4. Try `./install.sh` for automatic setup

### Import Errors

**Problem:** `ModuleNotFoundError` when running.

**Solution:**
```bash
# Activate virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Denied

**Problem:** Cannot run `./install.sh` or `./tad`.

**Solution:**
```bash
chmod +x install.sh
chmod +x tad
```

## Getting Help

- 📘 [User Guide](/guide/user-guide) - Complete command reference
- 🔧 [Troubleshooting](/guide/troubleshooting) - Common issues
- 💬 [GitHub Issues](https://github.com/fabriziosalmi/tad/issues) - Report bugs
- 📖 [Architecture](/reference/architecture) - Technical details

---

**Ready to dive deeper?** Continue to [Installation](/guide/installation) for detailed setup options.
