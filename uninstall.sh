#!/usr/bin/env bash

#####################################################################
# TAZCOM Uninstaller
# 
# This script removes TAZCOM from your system
# 
# Usage:
#   chmod +x uninstall.sh
#   ./uninstall.sh
#####################################################################

set -e
set -u

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_header() {
    echo -e "${RED}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║           TAZCOM Uninstaller                              ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_step() {
    echo -e "${GREEN}==>${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠ WARNING:${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    OS="unknown"
fi

print_header

echo "This will remove TAZCOM from your system."
echo
print_warning "The following will be deleted:"
echo "  • Python virtual environment (venv/)"
echo "  • Launcher script (tazcom)"
if [[ "$OS" == "linux" ]] && [[ -f "/etc/systemd/system/tazcom.service" ]]; then
    echo "  • Systemd service (/etc/systemd/system/tazcom.service)"
fi
echo
print_warning "The following will be PRESERVED:"
echo "  • Your identity (profile.json)"
echo "  • Message database (tad_node.db)"
echo "  • Source code (tad/)"
echo

read -p "Continue with uninstall? [y/N] " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

# Stop and remove systemd service
if [[ "$OS" == "linux" ]] && [[ -f "/etc/systemd/system/tazcom.service" ]]; then
    print_step "Removing systemd service..."
    
    if systemctl is-active --quiet tazcom; then
        sudo systemctl stop tazcom
        print_success "Service stopped"
    fi
    
    if systemctl is-enabled --quiet tazcom; then
        sudo systemctl disable tazcom
        print_success "Service disabled"
    fi
    
    sudo rm /etc/systemd/system/tazcom.service
    sudo systemctl daemon-reload
    print_success "Service removed"
fi

# Remove venv
if [[ -d "venv" ]]; then
    print_step "Removing virtual environment..."
    rm -rf venv
    print_success "Virtual environment removed"
fi

# Remove launcher
if [[ -f "tazcom" ]]; then
    print_step "Removing launcher..."
    rm tazcom
    print_success "Launcher removed"
fi

# Remove __pycache__
print_step "Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
print_success "Cache cleaned"

echo
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Uninstall Complete                              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo
echo "TAZCOM has been uninstalled."
echo
echo "Preserved files:"
echo "  • profile.json (your identity)"
echo "  • tad_node.db (message database)"
echo "  • tad/ (source code)"
echo "  • requirements.txt"
echo "  • install.sh, uninstall.sh"
echo
echo "To completely remove TAZCOM:"
echo "  cd .. && rm -rf tad/"
echo
