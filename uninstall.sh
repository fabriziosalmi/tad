#!/usr/bin/env bash

#####################################################################
# TAD Uninstaller
# 
# This script removes TAD from your system
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
    echo "║           TAD Uninstaller                              ║"
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

echo "This will remove TAD from your system."
echo
print_warning "The following will be deleted:"
echo "  • Python virtual environment (venv/)"
echo "  • Launcher script (tad)"
if [[ "$OS" == "linux" ]] && [[ -f "/etc/systemd/system/tad.service" ]]; then
    echo "  • Systemd service (/etc/systemd/system/tad.service)"
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
if [[ "$OS" == "linux" ]] && [[ -f "/etc/systemd/system/tad.service" ]]; then
    print_step "Removing systemd service..."
    
    if systemctl is-active --quiet tad; then
        sudo systemctl stop tad
        print_success "Service stopped"
    fi
    
    if systemctl is-enabled --quiet tad; then
        sudo systemctl disable tad
        print_success "Service disabled"
    fi
    
    sudo rm /etc/systemd/system/tad.service
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
if [[ -f "tad" ]]; then
    print_step "Removing launcher..."
    rm tad
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
echo "TAD has been uninstalled."
echo
echo "Preserved files:"
echo "  • profile.json (your identity)"
echo "  • tad_node.db (message database)"
echo "  • tad/ (source code)"
echo "  • requirements.txt"
echo "  • install.sh, uninstall.sh"
echo
echo "To completely remove TAD:"
echo "  cd .. && rm -rf tad/"
echo
