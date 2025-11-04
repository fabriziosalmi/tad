# Project Files Overview

This document provides a bird's-eye view of all files in the TAZCOM project, their purpose, and relationships.

---

## 📋 Documentation Files

### **README.md**
**Purpose:** Project vision, principles, and roadmap
**Audience:** New contributors, stakeholders
**Content:**
- Project manifesto (6 core principles)
- Feature descriptions (TribeNet, L'Eco, Whisper, VibeMap)
- Development roadmap (FASE 0-4)
- Initial technology stack

**When to update:** When adding new features or changing core vision

---

### **PROJECT_STATUS.md**
**Purpose:** Operational tracking and architectural decisions
**Audience:** Active developers
**Content:**
- Current phase status
- Architectural decisions (made and pending)
- Task tracking (completed, open, in progress)
- Blockers and risks
- Discovery log (learnings from implementation)

**When to update:** After completing major tasks or making architectural decisions

---

### **CLAUDE.md**
**Purpose:** Guidance for AI assistants (Claude Code) working in this repository
**Audience:** Claude Code, future instances, developers
**Content:**
- Project overview and principles
- Project structure (current and planned)
- Architectural constraints
- Development workflow and milestones
- Common commands (for when code structure exists)
- Risk areas and mitigation

**When to update:** After major structural changes or when adding new significant features

---

## 🔧 Implementation Files

### **poc-01_discovery.py** ✅
**Status:** Completed
**Phase:** FASE 0, Milestone 1
**Purpose:** TAZCOM node with cryptographic identity and service discovery

**Key Classes:**
- `TAZCOMNode` - Main node class with:
  - Ed25519 identity management
  - Zeroconf service publishing
  - Peer discovery via ServiceBrowser
  - Thread-safe peer list management

**Key Features:**
- Generates/persists Ed25519 key pairs for node identity
- Discovers peers via mDNS/Zeroconf on local network
- Maintains peer list with thread-safe locks
- Structured logging with Python `logging` module
- O(1) peer removal with inverse lookup table

**Dependencies:** `pynacl`, `zeroconf`

**How to Run:**
```bash
python poc-01_discovery.py
# Start in multiple terminals on same network to see discovery in action
```

**Output Example:**
```
[10:23:45] [INFO ] TAZCOM Node Initialized.
[10:23:45] [INFO ] Node ID: a1b2c3d4e5f6g7h8...
[10:23:45] [INFO ] Listening on 192.168.1.10:54321
[10:23:45] [INFO ] Publishing service 'TAZCOM Node a1b2c3d4._tazcom._tcp.local.'
[10:23:48] [INFO ] Peer Discovered: x9y8z7w6v5u4t3s2... @ 192.168.1.12:51234
```

---

### **poc-02_connection.py** ✅
**Status:** Completed
**Phase:** FASE 0, Milestone 2
**Purpose:** Extends poc-01 with TCP-based P2P messaging

**Key Classes:**
- `TAZCOMNode` (extended from poc-01) with:
  - TCP server (`asyncio.start_server`)
  - TCP client (`asyncio.open_connection`)
  - Message handling and protocol

**Key Methods:**
- `_start_tcp_server()` - Start listening for incoming connections
- `handle_connection(reader, writer)` - Server-side message handler
- `send_hello(peer_id)` - Send greeting to discovered peer
- Enhanced `_on_service_added()` - Auto-send HELLO on peer discovery

**Key Features:**
- Asynchronous TCP server on auto-allocated port
- Asynchronous TCP client for peer messaging
- JSON message format with newline delimiter
- Automatic HELLO handshake on peer discovery
- Graceful error handling (ConnectionRefused, Timeout, etc.)
- Structured logging and thread-safe operations

**Dependencies:** `pynacl`, `zeroconf`

**How to Run:**
```bash
python poc-02_connection.py
# Start in multiple terminals to observe auto-discovery and HELLO exchange
```

**Message Protocol:**
```json
// HELLO Message (Client → Server)
{"type": "HELLO", "from": "a1b2c3d4e5f6g7h8..."}

// ACK Response (Server → Client)
ACK
```

**Output Example:**
```
[10:23:47] [INFO ] TCP server started on 192.168.1.10:51234
[10:23:48] [INFO ] Peer Discovered: a1b2c3d4... @ 192.168.1.10:54321
[10:23:48] [INFO ] Sent HELLO to a1b2c3d4... @ 192.168.1.10:54321
[10:23:48] [INFO ] Message from ('192.168.1.10', 54321): {"type":"HELLO","from":"a1b2c3d4..."}
[10:23:48] [INFO ] Received ACK from a1b2c3d4...
```

---

## 📚 Guide & Reference Files

### **POC_02_GUIDE.md**
**Purpose:** Complete guide to understanding and running poc-02_connection
**Audience:** Developers wanting to understand/test poc-02
**Content:**
- Feature overview with code snippets
- Multi-node execution examples
- Complete event sequence timeline
- Data flow diagrams
- Error handling patterns
- Threading and concurrency model
- Troubleshooting guide
- Next steps (transition to poc-03)

**When to read:** Before running poc-02 for the first time, or when debugging

---

### **IMPROVEMENTS.md**
**Purpose:** Document enhancements made to poc-01 for robustness
**Audience:** Developers interested in code quality decisions
**Content:**
- Structured logging implementation
- Thread-safe peer management with locks
- O(1) peer removal optimization
- Event loop reference storage

**When to read:** When understanding threading complexity or learning best practices

---

### **FILES_OVERVIEW.md** (this file)
**Purpose:** High-level directory of all project files
**Audience:** All team members, especially new contributors
**Content:** File inventory with purposes and relationships

---

## 📦 Configuration & Dependency Files

### **requirements.txt**
**Purpose:** Python package dependencies
**Content:**
```
pynacl>=1.5.0
zeroconf>=0.40.0
```

**When to update:** When adding new external libraries

**How to use:**
```bash
pip install -r requirements.txt
```

---

### **node.key** (Auto-generated)
**Purpose:** Persist node identity across restarts
**Created by:** `poc-01_discovery.py` and `poc-02_connection.py` on first run
**Format:** JSON file containing:
```json
{
  "signing_key": "base64-encoded-ed25519-key",
  "created": "2025-11-04T10:23:45.123456"
}
```

**Important:** Do not share or commit this file (should be in `.gitignore`)

---

## 📊 File Relationship Diagram

```
README.md (Vision)
    └─ Contains manifesto and roadmap

PROJECT_STATUS.md (Status)
    └─ Tracks progress of milestones
    └─ References poc-01_discovery.py ✅
    └─ References poc-02_connection.py ✅
    └─ References poc-03_chat_basic (planned)

CLAUDE.md (AI Assistant Guide)
    └─ Points to README.md for vision
    └─ Points to PROJECT_STATUS.md for progress
    └─ Describes poc-01 and poc-02

poc-01_discovery.py ✅
    └─ Implements: Zeroconf discovery, Ed25519 identity
    └─ Uses: pynacl, zeroconf
    └─ Produces: node.key (identity file)
    └─ Base for: poc-02_connection.py

poc-02_connection.py ✅
    └─ Extends: poc-01_discovery.py
    └─ Adds: TCP server/client, JSON messaging
    └─ Uses: pynacl, zeroconf (same as poc-01)
    └─ Referenced by: POC_02_GUIDE.md

POC_02_GUIDE.md
    └─ Documents: poc-02_connection.py
    └─ Provides: Examples, troubleshooting, architecture

IMPROVEMENTS.md
    └─ Documents: Enhancements to poc-01
    └─ Covers: Logging, threading, optimization

requirements.txt
    └─ Lists: External dependencies for all PoCs
```

---

## 🎯 File Purpose by Audience

### **For New Contributors:**
1. Read `README.md` - Understand the vision
2. Read `CLAUDE.md` - Understand architecture and workflow
3. Read `PROJECT_STATUS.md` - See what's been done
4. Run `poc-01_discovery.py` or `poc-02_connection.py` - See it working

### **For Active Developers:**
1. Reference `PROJECT_STATUS.md` - Check current phase and blockers
2. Use `CLAUDE.md` - Understand constraints and decisions
3. Consult `POC_02_GUIDE.md` - Debug and understand implementation
4. Check `requirements.txt` - Install dependencies

### **For Code Reviewers:**
1. Check `IMPROVEMENTS.md` - Understand design decisions
2. Review `poc-01_discovery.py` and `poc-02_connection.py` - Evaluate code quality
3. Consult `POC_02_GUIDE.md` - Understand intended behavior

---

## 📈 Evolution Path

```
FASE 0: Protocol & PoC
├─ poc-01_discovery ✅ (Discovery layer)
├─ poc-02_connection ✅ (TCP communication layer)
└─ poc-03_chat_basic (TUI layer)

FASE 1: MVP - TribeNet
├─ Gossip protocol (message routing)
├─ Public channels (topic subscription)
└─ Private messages (direct P2P)

FASE 2: SAMU Relay
├─ Priority alert system
└─ State management (OPEN/ASSIGNED/RESOLVED)

FASE 3: UI & Packaging
├─ Cross-platform UI (Flutter/Kivy)
└─ App distribution (APK, exe, etc.)

FASE 4: Field Testing
└─ Real-world deployment
```

---

## ✅ Checklist for Next Phase

When implementing `poc-03_chat_basic`:

- [ ] Study `poc-02_connection.py` architecture
- [ ] Add `textual` to `requirements.txt`
- [ ] Extend message protocol to support generic message types (not just HELLO)
- [ ] Implement TUI layout with `textual` widgets
- [ ] Create broadcast message handler
- [ ] Add message history display
- [ ] Add peer list display (with online/offline status)
- [ ] Add text input for composing messages
- [ ] Test with 3+ nodes on same network
- [ ] Update `PROJECT_STATUS.md` with completion
- [ ] Create `POC_03_GUIDE.md` with usage instructions

---

## 🗂️ Planned Files (Future)

- `poc-03_chat_basic.py` - TUI chat application
- `POC_03_GUIDE.md` - Usage guide for poc-03
- `protocol.md` - Formal specification of TAZCOM message protocol
- `.gitignore` - Exclude node.key, __pycache__, etc.
- `tests/test_discovery.py` - Unit tests for discovery
- `tests/test_connection.py` - Unit tests for TCP communication
- `setup.py` / `pyproject.toml` - Python package configuration

---

## 📝 Summary

| File | Status | Purpose |
|------|--------|---------|
| README.md | 📄 | Project vision |
| PROJECT_STATUS.md | 🔄 | Development tracking |
| CLAUDE.md | 📄 | AI assistant guide |
| poc-01_discovery.py | ✅ | Peer discovery |
| poc-02_connection.py | ✅ | P2P messaging |
| POC_02_GUIDE.md | 📄 | Usage documentation |
| IMPROVEMENTS.md | 📄 | Design decisions |
| FILES_OVERVIEW.md | 📄 | This file |
| requirements.txt | 📄 | Dependencies |
| node.key | 🔐 | Auto-generated identity |

**Legend:** ✅ Implemented | 🔄 Active development | 📄 Documentation | 🔐 Auto-generated
