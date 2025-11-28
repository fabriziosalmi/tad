# Commands Reference

Complete reference for all TAD commands.

## General Commands

### `/help`
Display available commands and their usage.

```
> /help
```

**Output:**
```
Available commands:
  /peers - Show connected peers
  /channels - List all channels
  /switch <channel> - Switch to channel
  ...
```

### `/quit`
Exit TAD gracefully.

```
> /quit
```

Alternative: Press `Ctrl+C`

---

## Peer Commands

### `/peers`
List all connected peers with their addresses.

```
> /peers
```

**Output:**
```
Connected peers: 3
- peer_abc123: 192.168.1.100:8765
- peer_def456: 192.168.1.101:8765
- peer_ghi789: 192.168.1.102:8765
```

### `/ping <peer_id>`
Test connectivity to a specific peer.

```
> /ping peer_abc123
```

---

## Channel Commands

### `/channels`
List all available channels.

```
> /channels
```

**Output:**
```
Available channels:
* #general (current, 3 peers)
  #dev (2 peers)
  #random (private, 1 peer)
```

### `/create <channel>`
Create a new public channel.

```
> /create #team
```

**Output:**
```
[SYSTEM] Created channel #team
```

### `/switch <channel>`
Switch to a different channel.

```
> /switch #dev
```

**Output:**
```
[SYSTEM] Switched to #dev
```

### `/join <channel>`
Join an existing channel.

```
> /join #random
```

### `/leave [channel]`
Leave the current or specified channel.

```
> /leave
> /leave #random
```

---

## Private Channel Commands

### `/create-private <channel> <password>`
Create an end-to-end encrypted channel.

```
> /create-private #secret mypassword123
```

**Output:**
```
[SYSTEM] Created private channel #secret
[SYSTEM] Channel is E2E encrypted
```

### `/join-private <channel> <password>`
Join an existing private channel with password.

```
> /join-private #secret mypassword123
```

---

## Data Management Commands

### `/export [channel] [format]`
Export channel history to file.

```
> /export #general json
> /export #dev txt
> /export  # exports current channel
```

**Formats:**
- `json` - JSON format (default)
- `txt` - Plain text
- `md` - Markdown

**Output:**
```
[SYSTEM] Exported 150 messages to exports/general_20241128.json
```

### `/import <file>`
Import messages from a file.

```
> /import exports/general_20241128.json
```

**Output:**
```
[SYSTEM] Imported 150 messages to #general
```

### `/clear [channel]`
Clear message history (local only).

```
> /clear
> /clear #dev
```

⚠️ **Warning:** This only clears local history, not on other peers.

---

## Information Commands

### `/info [channel]`
Show channel information.

```
> /info #general
```

**Output:**
```
Channel: #general
Type: Public
Created: 2024-11-28 10:30:00
Messages: 1,234
Peers: 5
```

### `/whoami`
Display your node information.

```
> /whoami
```

**Output:**
```
Node ID: peer_abc123
Public Key: AbCdEf...
IP: 192.168.1.100
Port: 8765
Uptime: 2h 15m
```

### `/status`
Show network and sync status.

```
> /status
```

**Output:**
```
Network: Connected
Peers: 5 active
Channels: 3 joined
Messages: 1,234 total
Database: 2.5 MB
```

---

## Search Commands

### `/search <query>`
Search messages in current channel.

```
> /search roadmap
```

**Output:**
```
Found 3 messages:
[2024-11-28 10:30] Alice: Let's discuss the roadmap
[2024-11-28 11:45] Bob: Roadmap looks good
[2024-11-28 14:20] Carol: Updated roadmap docs
```

### `/search-all <query>`
Search across all channels.

```
> /search-all security
```

---

## Advanced Commands

### `/resync [channel]`
Force re-synchronization with peers.

```
> /resync
> /resync #general
```

### `/reconnect`
Reconnect to all peers.

```
> /reconnect
```

### `/broadcast <message>`
Send message to all channels.

```
> /broadcast Server maintenance in 10 minutes
```

⚠️ Use sparingly - sends to ALL channels.

---

## Administration Commands

### `/kick <peer_id>`
Block a peer (local only).

```
> /kick peer_abc123
```

### `/unblock <peer_id>`
Unblock a previously blocked peer.

```
> /unblock peer_abc123
```

---

## Keyboard Shortcuts

- `Ctrl+C` - Exit TAD
- `Ctrl+L` - Clear screen
- `↑` / `↓` - Scroll message history
- `Tab` - Auto-complete commands
- `Enter` - Send message

---

## Command Tips

💡 **Tab Completion**: Start typing a command and press Tab

💡 **Command History**: Use Up/Down arrows to recall previous commands

💡 **Aliases**: Some commands have shortcuts (e.g., `/q` for `/quit`)

💡 **Case Sensitivity**: Channel names are case-sensitive

## See Also

- [Basic Usage](/guide/basic-usage) - Getting started guide
- [Channels](/guide/channels) - Channel management
- [Private Channels](/guide/private-channels) - Encryption features
- [Export & Import](/guide/export-import) - Data backup
