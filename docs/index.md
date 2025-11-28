---
layout: home

hero:
  name: TAD
  text: Tactical Autonomous Zone Communications
  tagline: P2P decentralized chat for offline-first communities
  image:
    src: /logo.svg
    alt: TAD
  actions:
    - theme: brand
      text: Get Started
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/fabriziosalmi/tad

features:
  - icon: 🔌
    title: Zero Configuration
    details: Auto-discovery via mDNS. No servers, no accounts, no configuration. Just start and connect.
  
  - icon: 🔒
    title: End-to-End Encryption
    details: Private channels with AES-256-GCM encryption. Only invited members can read messages.
  
  - icon: 💾
    title: Message Persistence
    details: SQLite database stores all conversations. Export/import for backup and migration.
  
  - icon: 🌐
    title: Offline-First
    details: Works on local networks without internet. Perfect for TAZs, free parties, and autonomous zones.
  
  - icon: 🎨
    title: Advanced TUI
    details: Professional terminal interface with multi-channel support and keyboard shortcuts.
  
  - icon: ✅
    title: Production Ready
    details: 97 tests passing, 100% coverage. Battle-tested with comprehensive documentation.
---

## Quick Start

Install and run TAD in 30 seconds:

```bash
# Automatic installation
git clone https://github.com/fabriziosalmi/tad.git
cd tad
./install.sh

# Start chatting
./tad
```

Nodes on the same network will auto-discover each other!

## What is TAD?

TAD is a **peer-to-peer, decentralized chat system** designed for offline-first communication in environments where traditional infrastructure fails or is absent:

- 🎉 **Free parties** - Coordinate without cell service
- 🏕️ **TAZ (Temporary Autonomous Zones)** - Community self-organization
- 📢 **Protests & demonstrations** - Resilient communication
- 🌄 **Remote locations** - Chat on local networks

### Core Principles

1. **No Central Authority** - True peer-to-peer mesh networking
2. **Offline-First** - Works on local networks, no internet required
3. **Privacy by Design** - End-to-end encryption for private channels
4. **Resilience** - Gossip protocol ensures message delivery
5. **Simplicity** - Zero configuration, just works

## Architecture

```
┌─────────────┐     mDNS      ┌─────────────┐     Gossip     ┌─────────────┐
│   Node A    │◄────────────► │   Node B    │◄──────────────►│   Node C    │
│             │   Discovery   │             │   Protocol     │             │
│  • Ed25519  │               │  • X25519   │                │  • SQLite   │
│  • SQLite   │     TCP       │  • AES-GCM  │      TCP       │  • Textual  │
│  • Textual  │◄────────────► │  • Gossip   │◄──────────────►│  • Gossip   │
└─────────────┘   Messages    └─────────────┘    Messages    └─────────────┘
```

## Feature Status

**v1.0 - MVP** ✅ **COMPLETE**

- [x] mDNS peer discovery
- [x] Direct TCP connections  
- [x] Gossip protocol routing
- [x] Multi-channel chat
- [x] Private encrypted channels
- [x] Message persistence (SQLite)
- [x] Advanced TUI interface
- [x] Export/import functionality
- [x] 97 passing tests (100% coverage)

**Future - Future** 🔮

- [ ] Message search (/search command)
- [ ] Emoji reactions
- [ ] File sharing
- [ ] Voice messages
- [ ] Mobile apps

## Documentation

<div class="vp-doc">
  <div class="custom-block tip">
    <p class="custom-block-title">📚 Complete Documentation</p>
    <ul>
      <li><a href="/guide/getting-started">Getting Started</a> - Install and run TAD</li>
      <li><a href="/guide/user-guide">User Guide</a> - All commands and features</li>
      <li><a href="/guide/deployment">Deployment</a> - systemd, Docker, Raspberry Pi</li>
      <li><a href="/reference/architecture">Architecture</a> - Technical deep dive</li>
      <li><a href="/reference/api">API Reference</a> - Python modules and classes</li>
    </ul>
  </div>
</div>

## Community

- **GitHub**: [fabriziosalmi/tad](https://github.com/fabriziosalmi/tad)
- **Issues**: [Report bugs or request features](https://github.com/fabriziosalmi/tad/issues)
- **License**: MIT

---

*"The network is not something you use. The network is where you are. The network is us."*
