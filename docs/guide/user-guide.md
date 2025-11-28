# TAD User Guide

**Version:** v1.0 Complete (v1.0)
**Date:** November 28, 2025

---

## Table of Contents

1. [Introduction](#introduction)
2. [Quick Start](#quick-start)
3. [Installation](#installation)
4. [Basic Usage](#basic-usage)
5. [Command Reference](#command-reference)
6. [Channels & Tribes](#channels--tribes)
7. [Private Channels & Security](#private-channels--security)
8. [Message History & Export](#message-history--export)
9. [Keyboard Shortcuts](#keyboard-shortcuts)
10. [Troubleshooting](#troubleshooting)
11. [Advanced Topics](#advanced-topics)

---

## Introduction

**TAD** (Tactical Autonomous Zone Communications) is a peer-to-peer, decentralized chat system designed for offline-first communication. It works on local networks without internet access and provides end-to-end encrypted private channels.

### Key Features
- ✅ **Zero Configuration** - Auto-discovery via mDNS
- ✅ **Multi-Channel** - Organize conversations into Tribes
- ✅ **End-to-End Encryption** - Private channels with AES-256-GCM
- ✅ **Message Persistence** - SQLite database storage
- ✅ **Advanced TUI** - Professional terminal interface
- ✅ **Export/Import** - Backup and restore conversations

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start TAD
python -m tad.main

# 3. Nodes on the same network will auto-discover each other!
```

That's it! No configuration, no servers, no accounts.

---

## Installation

### Requirements
- **Python:** 3.8 or higher
- **OS:** Linux, macOS, Windows (with WSL recommended)
- **Network:** Wi-Fi or Ethernet (same local network)

### Step-by-Step

```bash
# Clone repository (or download ZIP)
git clone https://github.com/yourusername/tad.git
cd tad

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Test installation
python -m pytest tests/ -v

# Run TAD
python -m tad.main
```

### Dependencies

```
textual>=0.40.0        # TUI framework
pynacl>=1.5.0          # Cryptography (libsodium)
zeroconf>=0.100.0      # mDNS peer discovery
cryptography>=41.0.0   # AES-GCM encryption
```

---

## Basic Usage

### Starting TAD

```bash
python -m tad.main
```

On first run, TAD will:
1. Generate a cryptographic identity (Ed25519 + X25519 keys)
2. Create `profile.json` with your identity
3. Create `tad_node.db` SQLite database
4. Start peer discovery service
5. Open the TUI interface

### The Interface

```
┌─────────────────────────────────────────────────┐
│                 TAD v1.0                     │
├──────────┬────────────────────────┬─────────────┤
│          │                        │             │
│ Channels │    Message History     │   Peers     │
│          │                        │             │
│ #general │ [10:23] Alice: Hello!  │ 👤 Alice    │
│🔒#secret │ [10:24] You: Hi there! │ 👤 Bob      │
│ #dev     │ [10:25] Bob joined     │             │
│          │                        │             │
├──────────┴────────────────────────┴─────────────┤
│ > Type message or /help                         │
├─────────────────────────────────────────────────┤
│ Tab: Next | Shift+Tab: Prev | ?: Help | q: Quit│
└─────────────────────────────────────────────────┘
```

### Sending Messages

Just type your message and press Enter. It will be sent to the active channel.

```
> Hello, world!
```

### Using Commands

Commands start with `/`:

```
> /help                          # Show help
> /channels                      # List channels
> /join #dev                     # Join a channel
> /switch #dev                   # Switch to #dev
```

---

## Command Reference

### Channel Management

#### `/join <#channel>`
Subscribe to a channel to receive its messages.

```bash
/join #dev
/join #offtopic
```

**Example:**
```
> /join #dev
[SYSTEM] Joined #dev
```

---

#### `/leave <#channel>`
Unsubscribe from a channel.

```bash
/leave #dev
```

**Note:** You cannot leave `#general` (the default channel).

---

#### `/switch <#channel>` or `/s <#channel>`
Switch to a different channel. The switched channel becomes active.

```bash
/switch #dev
/s #general
```

**Keyboard Shortcut:** Tab (next) / Shift+Tab (previous)

---

#### `/channels`
List all channels you're subscribed to.

```bash
/channels
```

**Output:**
```
Subscribed channels:
  ▶ #general
    #dev
    #offtopic
```

---

### Private Channels

#### `/create <#channel> [public|private]`
Create a new channel. Default is public.

```bash
/create #myChannel              # Public
/create #secret private         # Private (encrypted)
```

**Private channels:**
- Use AES-256-GCM encryption
- Only invited members can read messages
- Show 🔒 icon in channel list

---

#### `/invite <node_id> <#channel>`
Invite a peer to a private channel. Only the channel owner can invite.

```bash
/invite alice_abc123 #secret
```

**How to get node_id:**
Use `/peers` to see connected peers and their IDs.

---

### Information

#### `/peers`
Show number of connected peers.

```bash
/peers
```

**Output:**
```
Connected peers: 3
```

---

#### `/help`
Show command reference and keyboard shortcuts.

```bash
/help
```

---

### Import/Export

#### `/export [#channel] [filename]`
Export messages to JSON file for backup.

```bash
/export                                    # All channels → tad_export_all_TIMESTAMP.json
/export #general                           # Only #general → tad_export_general_TIMESTAMP.json
/export #general messages.json             # Custom filename
/export messages.json                      # All channels → messages.json
```

**Output file structure:**
```json
{
  "export_date": "2025-11-28T14:30:00",
  "channel": "#general",
  "message_count": 42,
  "messages": [
    {
      "msg_id": "abc123...",
      "channel_id": "#general",
      "sender_id": "alice_xyz",
      "content": "Hello!",
      "timestamp": "2025-11-28T14:25:00",
      "signature": "...",
      "is_encrypted": false,
      "nonce": null
    }
  ]
}
```

---

#### `/import <filename>`
Import messages from JSON file.

```bash
/import messages.json
/import backup_20251128.json
```

**Features:**
- Auto-creates missing channels
- Skips duplicate messages (by msg_id)
- Refreshes active channel view

---

## Channels & Tribes

### What are Channels?

Channels (also called Tribes) organize conversations by topic. Each channel is independent:

- Messages sent to `#general` only appear in `#general`
- You can subscribe to multiple channels
- Switch between channels with `/switch` or Tab

### Default Channels

Every node starts subscribed to:
- `#general` - Main discussion channel (cannot leave)

### Creating Channels

Anyone can create a public channel:

```bash
/create #dev
/create #random
```

### Joining Channels

There are two ways to join a channel:

1. **Create it:**
   ```bash
   /create #newChannel
   ```

2. **Join existing:**
   ```bash
   /join #dev
   ```

**Note:** For public channels, you can join even if you haven't seen it yet. For private channels, you need an invitation.

---

## Private Channels & Security

### Why Private Channels?

Private channels provide **end-to-end encryption** for sensitive conversations:

- ✅ Only invited members can read messages
- ✅ Non-members see garbled ciphertext
- ✅ AES-256-GCM authenticated encryption
- ✅ Forward secrecy (future: key rotation)

### Creating a Private Channel

```bash
/create #secret private
```

You become the **owner** with these permissions:
- Invite new members (`/invite`)
- Full read/write access

### Inviting Members

1. **Get the peer's node ID:**
   ```bash
   /peers
   ```

2. **Invite them:**
   ```bash
   /invite alice_abc123 #secret
   ```

3. **They auto-join** when they receive the invite

### Security Model

**What's Protected:**
- Message content (encrypted with AES-256-GCM)
- Channel key (exchanged via X25519 SealedBox)
- Message authenticity (Ed25519 signatures)

**What's Visible:**
- Channel ID (e.g., "#secret")
- Sender ID
- Message size and timing

### Key Management

- **Channel Key:** 256-bit symmetric key (one per private channel)
- **Signing Keys:** Ed25519 (for message signatures)
- **Encryption Keys:** X25519 (for key exchange)

Keys are stored:
- **On Disk:** `profile.json` (signing/encryption keys)
- **In Memory:** Channel keys (during runtime)
- **In Messages:** Encrypted channel keys (for invites)

---

## Message History & Export

### Message Storage

All messages are saved in `tad_node.db` (SQLite):

- Organized by channel
- Includes sender, timestamp, signature
- Encrypted messages stored as ciphertext
- Survives node restarts

### Loading History

When you switch to a channel, TAD automatically loads the last 50 messages:

```bash
/switch #dev
```

**Output:**
```
[SYSTEM] Loading history for #dev...
[10:20] Alice: Previous message 1
[10:21] Bob: Previous message 2
...
[SYSTEM] Switched to #dev
```

### Export Messages

**Use Case:** Backup before system upgrade

```bash
/export                  # Backup all channels
```

**Result:**
```
✓ Exported 156 messages to /Users/you/tad_export_all_20251128_143000.json
```

### Import Messages

**Use Case:** Restore after reinstall

```bash
/import tad_export_all_20251128_143000.json
```

**Result:**
```
✓ Imported 156/156 messages from tad_export_all_20251128_143000.json
```

### Export Format

Exports are standard JSON, safe to:
- ✅ Archive for long-term storage
- ✅ Import on another device
- ✅ Parse with external tools
- ✅ Version control (if not private)

**Warning:** Exported private channel messages contain **encrypted** content. You need the channel key to decrypt them.

---

## Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `Tab` | Next channel |
| `Shift+Tab` | Previous channel |
| `↑` / `↓` | Scroll message history |
| `Page Up` / `Page Down` | Fast scroll |

### Actions

| Key | Action |
|-----|--------|
| `Enter` | Send message / Execute command |
| `Ctrl+C` | Quit application |
| `?` | Show help |
| `q` | Quit (alternative) |

### TUI Interactions

- **Mouse Click:** Select channel (if terminal supports it)
- **Scroll Wheel:** Scroll message history
- **Resize Window:** Auto-adjusts layout

---

## Troubleshooting

### Nodes Not Discovering Each Other

**Problem:** Started TAD but no peers appear.

**Solutions:**

1. **Check Network:**
   - Ensure both devices on **same Wi-Fi/LAN**
   - Try `ping <other-ip>` to verify connectivity

2. **Check Firewall:**
   - Allow Python/TAD through firewall
   - Open UDP port 5353 (mDNS)
   - Open TCP ports 50000-60000 (dynamic ports)

3. **Check mDNS Service:**
   ```bash
   # macOS/Linux
   dns-sd -B _tad._tcp
   
   # Should show TAD nodes
   ```

4. **Restart Nodes:**
   - Exit TAD (Ctrl+C)
   - Wait 5 seconds
   - Restart: `python -m tad.main`

---

### Messages Not Sending

**Problem:** Type message but nothing happens.

**Solutions:**

1. **Check Active Channel:**
   - Verify correct channel selected
   - Use `/channels` to list subscribed channels

2. **Check Peers:**
   - Use `/peers` to see if peers connected
   - At least 1 peer needed to receive messages

3. **Check Logs:**
   ```bash
   # Run with debug logging
   python -m tad.main --log-level DEBUG
   ```

---

### Cannot Decrypt Private Channel

**Problem:** Receive encrypted messages but see garbled text.

**Causes:**
- ❌ Not invited to channel
- ❌ Lost channel key (database corruption)
- ❌ Wrong decryption key

**Solutions:**

1. **Request Re-Invite:**
   - Ask channel owner to `/invite` you again

2. **Check Database:**
   ```bash
   sqlite3 tad_node.db "SELECT * FROM channel_members WHERE node_id='YOUR_ID';"
   ```

3. **Verify Identity:**
   - Ensure `profile.json` intact
   - Backup and regenerate if corrupted

---

### Import Fails

**Problem:** `/import` command shows error.

**Solutions:**

1. **Check File Format:**
   - Must be valid JSON
   - Use `/export` to see correct format

2. **Check File Path:**
   ```bash
   /import /full/path/to/messages.json
   ```

3. **Check Permissions:**
   - Ensure read access to file
   - Ensure write access to database

---

## Advanced Topics

### Identity Files

**profile.json** - Your cryptographic identity

```json
{
  "version": "1.0",
  "username": "Alice",
  "signing_key": "hex_encoded_ed25519_private_key",
  "verify_key": "hex_encoded_ed25519_public_key",
  "encryption_private_key": "hex_encoded_x25519_private_key",
  "encryption_public_key": "hex_encoded_x25519_public_key"
}
```

**⚠️ CRITICAL:** Backup this file! Losing it means:
- ❌ New identity required
- ❌ Cannot decrypt old private channels
- ❌ Others see you as a new user

---

### Database Schema

**tad_node.db** - SQLite database with 3 tables:

1. **channels** - Channel metadata
   ```sql
   channel_id | name | type | owner_node_id | created_at | subscribed
   ```

2. **channel_members** - Membership & permissions
   ```sql
   channel_id | node_id | role | joined_at
   ```

3. **messages** - Message history
   ```sql
   msg_id | channel_id | sender_id | content | timestamp | signature | is_encrypted | nonce
   ```

**Backup:**
```bash
cp tad_node.db tad_node.db.backup
```

---

### Custom Port Configuration

By default, TAD uses random available ports. To specify:

```python
# In tad/node.py, modify __init__
self.tcp_port = 5000  # Fixed port
```

**Use Case:** Firewall rules, port forwarding

---

### Running as Service

**systemd (Linux):**

```ini
# /etc/systemd/system/tad.service
[Unit]
Description=TAD P2P Chat
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/home/youruser/tad
ExecStart=/usr/bin/python3 -m tad.main
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable tad
sudo systemctl start tad
```

---

### Network Diagnostics

**Check Discovery:**
```bash
dns-sd -B _tad._tcp
```

**Check Connections:**
```bash
netstat -an | grep ESTABLISHED
```

**Monitor Traffic:**
```bash
tcpdump -i en0 port 5353  # mDNS
```

---

## FAQ

**Q: Do I need internet access?**
A: No! TAD works on local networks without internet.

**Q: Can I use this over the internet?**
A: Not directly. You'd need VPN or port forwarding (not recommended without additional security).

**Q: How many peers can I have?**
A: Tested with 10-20 peers. Theoretically hundreds, limited by network bandwidth.

**Q: Are messages encrypted?**
A: Private channels: Yes (AES-256-GCM). Public channels: No (plaintext).

**Q: Can I change my username?**
A: Edit `profile.json` and restart. But others track you by public key, not username.

**Q: What if I lose profile.json?**
A: Generate new identity. Old private channels inaccessible.

**Q: Can I run multiple nodes on same computer?**
A: Yes! Use different directories:
```bash
cd ~/tad1 && python -m tad.main &
cd ~/tad2 && python -m tad.main &
```

---

## Getting Help

- **GitHub Issues:** https://github.com/yourusername/tad/issues
- **Documentation:** See `README.md`, `FASE_1_COMPLETE.md`
- **Logs:** Check terminal output, enable DEBUG level
- **Community:** (Future: Discord/Matrix)

---

## License

MIT License - See LICENSE file

---

**Happy Chatting! 🎉**

*For developers: See FASE_1_COMPLETE.md for technical architecture*
