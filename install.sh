#!/usr/bin/env bash

#####################################################################
# TAD Automatic Installer
# 
# This script automates the installation of TAD on Linux/macOS
# 
# Usage:
#   chmod +x install.sh
#   ./install.sh
#
# Features:
#   - Checks Python version (>=3.8)
#   - Creates virtual environment
#   - Installs dependencies
#   - Runs test suite
#   - Optionally installs systemd service (Linux only)
#####################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MIN_PYTHON_VERSION="3.8"
VENV_DIR="venv"
INSTALL_DIR="${INSTALL_DIR:-$(pwd)}"
SYSTEMD_DIR="/etc/systemd/system"
SERVICE_NAME="tad.service"

#####################################################################
# Helper Functions
#####################################################################

print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           TAD Automatic Installer v1.0                 ║"
    echo "║   Tactical Autonomous Zone Communications                  ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}✗ ERROR:${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

#####################################################################
# Checks
#####################################################################

check_os() {
    print_step "Detecting operating system..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        print_success "Linux detected"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        print_success "macOS detected"
    else
        print_error "Unsupported OS: $OSTYPE"
        print_warning "TAD is designed for Linux and macOS"
        exit 1
    fi
}

check_python() {
    print_step "Checking Python installation..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 not found. Please install Python ${MIN_PYTHON_VERSION} or higher."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d. -f1)
    PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d. -f2)
    
    if [[ "$PYTHON_MAJOR" -lt 3 ]] || { [[ "$PYTHON_MAJOR" -eq 3 ]] && [[ "$PYTHON_MINOR" -lt 8 ]]; }; then
        print_error "Python ${PYTHON_VERSION} found, but ${MIN_PYTHON_VERSION}+ required"
        exit 1
    fi
    
    print_success "Python ${PYTHON_VERSION} found"
}

check_dependencies() {
    print_step "Checking system dependencies..."
    
    # Check if we can compile native extensions (needed for pynacl)
    if command -v gcc &> /dev/null || command -v clang &> /dev/null; then
        print_success "C compiler found"
    else
        print_warning "No C compiler found. Native extension compilation may fail."
        print_warning "On Debian/Ubuntu: sudo apt-get install build-essential"
        print_warning "On macOS: xcode-select --install"
    fi
    
    # Check for libsodium (optional, pynacl can build it)
    if [[ "$OS" == "linux" ]] && ! ldconfig -p | grep -q libsodium; then
        print_warning "libsodium not found. Will be built by pynacl (slower install)."
        print_warning "Optional: sudo apt-get install libsodium-dev"
    fi
}

#####################################################################
# Installation
#####################################################################

create_venv() {
    print_step "Creating Python virtual environment..."
    
    if [[ -d "$VENV_DIR" ]]; then
        print_warning "Virtual environment already exists at ${VENV_DIR}"
        read -p "Remove and recreate? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_DIR"
        else
            print_warning "Skipping venv creation"
            return
        fi
    fi
    
    python3 -m venv "$VENV_DIR"
    print_success "Virtual environment created at ${VENV_DIR}"
}

install_dependencies() {
    print_step "Installing Python dependencies..."
    
    # Activate venv
    source "${VENV_DIR}/bin/activate"
    
    # Upgrade pip
    print_step "Upgrading pip..."
    pip install --upgrade pip
    
    # Install dependencies
    print_step "Installing requirements..."
    pip install -r requirements.txt
    
    print_success "Dependencies installed"
}

run_tests() {
    print_step "Running test suite..."
    
    source "${VENV_DIR}/bin/activate"
    
    if python -m pytest tests/ -v --tb=short; then
        print_success "All tests passed! ✓"
    else
        print_error "Some tests failed"
        read -p "Continue anyway? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

#####################################################################
# Systemd Service (Linux only)
#####################################################################

install_systemd_service() {
    if [[ "$OS" != "linux" ]]; then
        print_warning "Systemd service installation only available on Linux"
        return
    fi
    
    print_step "Installing systemd service..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_warning "Systemd service installation requires root privileges"
        read -p "Install service with sudo? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_warning "Skipping systemd service installation"
            return
        fi
        SUDO="sudo"
    else
        SUDO=""
    fi
    
    # Get current user for service
    if [[ -n "${SUDO}" ]]; then
        SERVICE_USER="$USER"
    else
        read -p "Run TAD as user [default: $USER]: " SERVICE_USER
        SERVICE_USER="${SERVICE_USER:-$USER}"
    fi
    
    # Create service file
    cat > "/tmp/${SERVICE_NAME}" <<EOF
[Unit]
Description=TAD P2P Chat Service
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/${VENV_DIR}/bin/python -m tad.main
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=${INSTALL_DIR}

[Install]
WantedBy=multi-user.target
EOF
    
    # Install service
    $SUDO cp "/tmp/${SERVICE_NAME}" "${SYSTEMD_DIR}/${SERVICE_NAME}"
    $SUDO systemctl daemon-reload
    
    print_success "Systemd service installed at ${SYSTEMD_DIR}/${SERVICE_NAME}"
    
    # Ask to enable/start
    read -p "Enable service on boot? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $SUDO systemctl enable "${SERVICE_NAME}"
        print_success "Service enabled on boot"
    fi
    
    read -p "Start service now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        $SUDO systemctl start "${SERVICE_NAME}"
        print_success "Service started"
        echo
        echo "Check status with: sudo systemctl status ${SERVICE_NAME}"
        echo "View logs with: sudo journalctl -u ${SERVICE_NAME} -f"
    fi
}

#####################################################################
# Launcher Script
#####################################################################

create_launcher() {
    print_step "Creating launcher script..."
    
    cat > "tad" <<'EOF'
#!/usr/bin/env bash
# TAD Launcher Script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/venv/bin/activate"
exec python -m tad.main "$@"
EOF
    
    chmod +x tad
    print_success "Launcher created: ./tad"
}

#####################################################################
# Post-Install
#####################################################################

print_summary() {
    echo
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           Installation Complete! 🎉                        ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    echo
    echo "TAD has been successfully installed!"
    echo
    echo "Quick Start:"
    echo "  1. Run TAD:      ./tad"
    echo "  2. Or manually:     source venv/bin/activate && python -m tad.main"
    echo
    if [[ "$OS" == "linux" ]] && [[ -f "${SYSTEMD_DIR}/${SERVICE_NAME}" ]]; then
        echo "Systemd Service:"
        echo "  • Status:   sudo systemctl status tad"
        echo "  • Start:    sudo systemctl start tad"
        echo "  • Stop:     sudo systemctl stop tad"
        echo "  • Logs:     sudo journalctl -u tad -f"
        echo
    fi
    echo "Documentation:"
    echo "  • User Guide:       USER_GUIDE.md"
    echo "  • Technical Docs:   FASE_1_COMPLETE.md"
    echo "  • Getting Started:  README.md"
    echo
    echo "Get Help:"
    echo "  • Commands:         Type /help in TAD"
    echo "  • Issues:           https://github.com/yourusername/tad/issues"
    echo
}

#####################################################################
# Main Installation Flow
#####################################################################

main() {
    print_header
    
    # Checks
    check_os
    check_python
    check_dependencies
    
    echo
    
    # Installation
    create_venv
    install_dependencies
    
    echo
    
    # Testing
    read -p "Run test suite? [Y/n] " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Nn]$ ]]; then
        run_tests
    fi
    
    echo
    
    # Optional: Systemd service
    if [[ "$OS" == "linux" ]]; then
        read -p "Install systemd service? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            install_systemd_service
        fi
    fi
    
    echo
    
    # Create launcher
    create_launcher
    
    # Summary
    print_summary
}

# Run main
main "$@"
