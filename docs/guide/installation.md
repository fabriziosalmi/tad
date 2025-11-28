# Installation

Detailed installation instructions for different scenarios.

## Prerequisites

### System Requirements

- **Operating System:** Linux, macOS, or Windows (WSL recommended)
- **Python:** 3.8 or higher
- **RAM:** 512 MB minimum
- **Disk:** 50 MB for application + database
- **Network:** Wi-Fi or Ethernet adapter

### Check Python Version

```bash
python3 --version
# Should output: Python 3.8.0 or higher
```

If Python is not installed:

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python3
```

**Windows:**
Download from [python.org](https://www.python.org/downloads/)

## Installation Methods

### Method 1: Automatic Installer (Recommended)

The easiest way to install TAD:

```bash
git clone https://github.com/fabriziosalmi/tad.git
cd tad
chmod +x install.sh
./install.sh
```

The installer will:
1. ✅ Check Python version
2. ✅ Create virtual environment  
3. ✅ Install all dependencies
4. ✅ Run test suite
5. ✅ Create launcher script
6. ✅ Optionally install systemd service (Linux)

### Method 2: Manual Installation

For more control over the installation process:

```bash
# 1. Clone repository
git clone https://github.com/fabriziosalmi/tad.git
cd tad

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install dependencies
pip install -r requirements.txt

# 6. Verify installation
python -m pytest tests/ -v

# 7. Run TAD
python -m tad.main
```

### Method 3: System-Wide Installation

For multi-user systems:

```bash
# Install to /opt (requires root)
sudo git clone https://github.com/fabriziosalmi/tad.git /opt/tad
cd /opt/tad

# Create dedicated user
sudo useradd -r -s /bin/false tad

# Run installer
sudo ./install.sh

# Set permissions
sudo chown -R tad:tad /opt/tad

# Create global launcher
sudo ln -s /opt/tad/tad /usr/local/bin/tad

# Now any user can run
tad
```

## Dependency Details

TAD requires these Python packages:

```txt
textual>=0.40.0        # Terminal UI framework
pynacl>=1.5.0          # Cryptography (libsodium)
zeroconf>=0.100.0      # mDNS peer discovery
cryptography>=41.0.0   # AES-GCM encryption
pytest>=7.4.0          # Testing (development)
pytest-asyncio>=0.21.0 # Async tests (development)
```

### Optional System Dependencies

**libsodium** (improves pynacl performance):

```bash
# Ubuntu/Debian
sudo apt install libsodium-dev

# macOS
brew install libsodium

# Not required - pynacl will build it if missing
```

**Avahi** (for better mDNS on Linux):

```bash
# Ubuntu/Debian
sudo apt install avahi-daemon

# Fedora/RHEL
sudo dnf install avahi
```

## Verification

### Test Installation

```bash
# Activate virtual environment
source venv/bin/activate

# Run tests
python -m pytest tests/ -v

# Expected output:
# ===== 97 passed in X.XXs =====
```

### Check Imports

```bash
python -c "
from tad.node import TADNode
from tad.crypto.e2ee import E2EEManager
from tad.network.discovery import DiscoveryService
print('✓ All imports successful')
"
```

### Generate Identity

```bash
# Run TAD once to generate identity
python -m tad.main

# Check files created
ls -la profile.json tad_node.db
```

## Post-Installation

### Directory Structure

After installation, you should have:

```
tad/
├── venv/               # Virtual environment
├── tad/                # Source code
│   ├── __init__.py
│   ├── main.py
│   ├── node.py
│   ├── identity.py
│   ├── crypto/
│   ├── network/
│   ├── persistence/
│   └── ui/
├── tests/              # Test suite
├── docs/               # Documentation
├── profile.json        # Your identity (created on first run)
├── tad_node.db         # Message database (created on first run)
├── tad              # Launcher script
├── install.sh          # Installer
├── uninstall.sh        # Uninstaller
└── requirements.txt    # Dependencies
```

### Important Files

**profile.json** - Your cryptographic identity
- 🔑 Contains signing and encryption keys
- ⚠️ **BACKUP THIS FILE!** Losing it means new identity
- 🔒 Keep private (contains private keys)

**tad_node.db** - Your message database
- 💾 SQLite database with all messages
- 📦 Can be backed up with `/export` command
- 🔄 Portable across devices

## Updating TAD

### Standard Installation

```bash
cd tad
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade
```

### System-Wide Installation

```bash
sudo systemctl stop tad  # If running as service
cd /opt/tad
sudo git pull
sudo -u tad ./venv/bin/pip install -r requirements.txt --upgrade
sudo systemctl start tad
```

## Uninstallation

### Using Uninstaller

```bash
./uninstall.sh
```

This removes:
- ✅ Virtual environment
- ✅ Launcher script
- ✅ Systemd service (if installed)

This preserves:
- ⚠️ profile.json (your identity)
- ⚠️ tad_node.db (your messages)
- ⚠️ Source code

### Complete Removal

```bash
# Uninstall first
./uninstall.sh

# Then remove everything
cd ..
rm -rf tad/
```

## Troubleshooting

### Python Version Too Old

**Error:** `Python 3.7 found, but 3.8+ required`

**Solution:**
```bash
# Use pyenv to install newer Python
curl https://pyenv.run | bash
pyenv install 3.11.0
pyenv local 3.11.0
```

### Permission Errors

**Error:** `Permission denied: '/opt/tad'`

**Solution:**
```bash
# Use sudo for system-wide install
sudo ./install.sh

# Or install in home directory
cd ~
git clone https://github.com/fabriziosalmi/tad.git
cd tad
./install.sh
```

### Dependency Installation Fails

**Error:** `Failed building wheel for pynacl`

**Solution:**
```bash
# Install build tools
# Ubuntu/Debian:
sudo apt install build-essential python3-dev libsodium-dev

# macOS:
xcode-select --install
brew install libsodium
```

### Virtual Environment Issues

**Error:** `No module named 'venv'`

**Solution:**
```bash
# Install venv module
# Ubuntu/Debian:
sudo apt install python3-venv

# Then retry
python3 -m venv venv
```

## Next Steps

- 🚀 [Quick Start](/guide/quick-start) - Start using TAD
- 📖 [User Guide](/guide/user-guide) - Learn all commands
- 🔧 [Deployment](/guide/deployment) - Production setups
- 🐳 [Docker](/guide/docker) - Container deployment

---

**Need help?** Open an issue on [GitHub](https://github.com/fabriziosalmi/tad/issues).
