# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TAZCOM** (Tactical Autonomous Zone Communications) is a decentralized, offline-first tactical communication system designed for Temporary Autonomous Zones, free parties, and community self-organization. Currently in **FASE 0 (Conceptual/Prototyping)** - no production code yet.

**Key Principle:** Offline-first mesh networking with zero configuration, real anonymity, ephemeral communications, and end-to-end encryption.

### Core Technologies
- **Language:** Python 3 (3.8+ target)
- **Cryptography:** `pynacl` (Ed25519 key pairs for node identity)
- **Service Discovery:** `zeroconf` (mDNS for local network discovery)
- **UI Framework:** `textual` (Terminal User Interface for TUI applications)
- **Transport (PoC):** TCP sockets; Future: BLE, Wi-Fi Direct
- **Message Format:** JSON

## Project Structure

The project is currently **documentation-focused** with no source code directories yet:

```
/fan
├── README.md              # Vision, principles, and feature roadmap
├── PROJECT_STATUS.md      # Operational log, decisions, and task tracking
└── CLAUDE.md              # This file
```

### Key Documentation Files
- **README.md:** Project manifesto, core principles (Offline First, Zero Configuration, Real Anonymity, Ephemeral, E2E Encryption, Low Power), feature descriptions (TribeNet, L'Eco, Whisper, VibeMap), and development roadmap
- **PROJECT_STATUS.md:** Current phase status, architectural decisions made, open tasks, blockers, and discovery log

## Architectural Decisions

### Decided (Solid Choices)
- **Cryptographic Identity:** Ed25519 key pairs; Verify Key serves as public node ID
- **Service Discovery:** mDNS/Zeroconf (consolidated standard, library stable)
- **Initial Transport:** TCP sockets (reliable, simple for PoC; future alternatives: UDP, WebSockets)
- **Message Format:** JSON (human-readable, excellent for debugging in Phase 0)
- **Node Architecture:** Fully decentralized; every device is a peer with its own identity

### Pending Decisions
- **Higher-level Messaging Protocol:** Design details of gossip protocol, message routing, and conflict resolution
- **Future Radio Layers:** BLE vs Wi-Fi Direct support strategy
- **Session Management:** How to handle peer discovery/disconnection edge cases
- **NAT Traversal:** Deferred until LAN-only PoC is stable

## Development Workflow

### Current Phase: FASE 0 (Protocol & PoC)
**Goal:** Validate that multiple nodes can discover each other, communicate via TCP, and exchange messages over a local network without manual configuration.

**PoC Milestones (All Completed):**
1. ✅ **poc-01_discovery** - mDNS service publishing and peer discovery
   - File: `poc-01_discovery.py`
   - Features: Zeroconf registration, peer discovery via ServiceBrowser, thread-safe peer management

2. ✅ **poc-02_connection** - Direct TCP P2P connection and messaging
   - File: `poc-02_connection.py`
   - Features: Async TCP server, async TCP client, JSON message protocol, automatic HELLO handshake
   - Guide: `POC_02_GUIDE.md` with examples and troubleshooting

3. ✅ **poc-03_chat_basic** - Interactive TUI chat application
   - File: `poc-03_chat_basic.py`
   - Features: Textual TUI with peer list, message history, real-time input, CHAT message type
   - Guide: `POC_03_GUIDE.md` with UI layout and usage examples
   - Status: Complete and tested

### Future Phases
- **FASE 1:** MVP - TribeNet (gossip protocol + public channel chat)
- **FASE 2:** SAMU Relay (priority alert system with state management)
- **FASE 3:** UI & Packaging (cross-platform GUI, APK/executable)
- **FASE 4:** Field testing with real users

## Common Commands (When Code Structure is Established)

Once the Python package structure is created, the following commands will be relevant:

```bash
# Install dependencies (when pyproject.toml/requirements.txt exists)
pip install -e .
pip install -e ".[dev]"  # includes test/lint dependencies

# Run the TUI application (once implemented)
python -m tazcom

# Run tests (when test suite is created)
pytest
pytest -v                 # verbose
pytest path/to/test.py   # single test file

# Code quality checks (when configured)
black --check src/
flake8 src/
mypy src/
pylint src/

# Format code
black src/
```

## Important Architectural Constraints

### Design Principles (Non-Negotiable)
1. **Offline First:** Every feature must function without internet or cellular
2. **Zero Configuration:** Users should not need to enter IPs, passwords, or account details
3. **Real Anonymity:** No connection to personal data; cryptographic identity only
4. **Ephemeral Nature:** Messages should have TTL; data shouldn't persist permanently
5. **End-to-End Encryption:** All communications encrypted; no plain-text transmission
6. **Low Power Consumption:** Optimized for multi-day events on phone batteries

### Networking Assumptions (Current Phase)
- Devices are on the same local network (Wi-Fi or wired)
- mDNS works reliably on the local network
- TCP port assignment is dynamic; broadcast via mDNS TXT records
- No NAT traversal needed for PoC (single LAN only)

## Key Files & What They Contain

| File | Purpose | Key Sections |
|------|---------|--------------|
| README.md | Project vision and roadmap | Principles, feature descriptions, stack choices |
| PROJECT_STATUS.md | Development tracking and decisions | Phase status, decisions, open tasks, blockers |

## Risk Areas & Mitigation Strategies

### Known Blockers
1. **Networking Complexity:** NAT traversal is complex across different network types (deferred until post-PoC)
2. **Cross-Platform Low-Level Networking:** BLE/Wi-Fi Direct drivers behave differently per OS (mitigated by starting with mDNS)
3. **Battery Consumption:** Continuous Wi-Fi usage drains batteries quickly (post-PoC optimization focus)

### De-Risking Strategy
The current PoC focuses on mDNS + TCP over LAN to validate the core communication layer before tackling the complexity of truly offline scenarios (BLE/Wi-Fi Direct) and power optimization.

## Code Style & Patterns (To Be Established)

When implementing Phase 1+ code:
- Use type hints (Python 3.8+ supports them well)
- Follow PEP 8 / Black formatting
- Async-first design (needed for responsive TUI and concurrent network operations)
- Event-driven architecture (aligns with Textual framework)
- Cryptographic operations should use pynacl exclusively (never roll custom crypto)

## Important Notes

- **Phase 0 is NOT about production-quality code.** Focus is on validation and learning. Expect to refactor heavily in Phase 1.
- **The project is Italian in spirit** (TAZ, free parties, community culture) but code and documentation are in English for broader collaboration.
- **License is MIT** - permissive open-source with no restrictions.
- **This is a real project with real-world applications** - not an academic exercise. Field testing with actual users is planned.
