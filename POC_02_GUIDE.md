# POC-02: Direct P2P TCP Communication - User Guide

## Overview

**poc-02_connection.py** extends the service discovery mechanism from poc-01 to enable actual TCP communication between TAZCOM nodes. Each node now:

1. ✅ Generates a unique cryptographic identity (Ed25519)
2. ✅ Publishes itself via mDNS/Zeroconf
3. ✅ Discovers other TAZCOM nodes
4. ✅ **Runs an asynchronous TCP server** (NEW)
5. ✅ **Sends/receives messages** (NEW)
6. ✅ **Automatically exchanges HELLO messages** (NEW)

---

## Key Features

### 1. **TCP Server**

Each node runs an embedded `asyncio` TCP server listening on `self.local_ip:self.tcp_port`.

```python
async def _start_tcp_server(self) -> None:
    self.server = await asyncio.start_server(
        self.handle_connection, self.local_ip, self.tcp_port
    )
```

**Responsibilities:**
- Accept incoming connections from peers
- Read a single message (up to 1024 bytes, delimited by newline)
- Log the message and sender address
- Respond with `ACK\n`
- Properly close the connection

### 2. **TCP Client**

Each node can initiate connections to discovered peers and send messages.

```python
async def send_hello(self, peer_id: str) -> None:
    reader, writer = await asyncio.open_connection(peer_ip, peer_port)
    writer.write(message_bytes)
    await writer.drain()
    ack_data = await reader.readuntil(b"\n")
```

**Features:**
- Thread-safe peer lookup (using `self.peers_lock`)
- JSON-formatted messages
- Error handling for `ConnectionRefusedError`, `TimeoutError`, etc.
- Graceful cleanup

### 3. **Automatic HELLO Handshake**

When a peer is discovered, the node automatically sends a HELLO message:

```python
async def _on_service_added(self, ...):
    # Add peer to dictionary
    async with self.peers_lock:
        self.peers[peer_id] = {...}

    # Automatically send HELLO
    await self.send_hello(peer_id)
```

This creates a natural peer-to-peer greeting mechanism.

---

## Message Format

### HELLO Message (Client → Server)

```json
{
    "type": "HELLO",
    "from": "a1b2c3d4e5f6g7h8..."
}
```

Transmitted as: `{"type":"HELLO","from":"..."}\n`

### ACK Response (Server → Client)

```
ACK
```

---

## Running Multiple Nodes

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Start Node #1
```bash
# Terminal 1
python poc-02_connection.py
```

Expected output:
```
[10:23:45] [INFO ] TAZCOM Node Initialized.
[10:23:45] [INFO ] Node ID: a1b2c3d4e5f6g7h8...
[10:23:45] [INFO ] Listening on 192.168.1.10:54321
[10:23:45] [INFO ] TCP server started on 192.168.1.10:54321
[10:23:45] [INFO ] Publishing service 'TAZCOM Node a1b2c3d4._tazcom._tcp.local.'
```

### Step 3: Start Node #2
```bash
# Terminal 2
python poc-02_connection.py
```

Expected output:
```
[10:23:47] [INFO ] TAZCOM Node Initialized.
[10:23:47] [INFO ] Node ID: x9y8z7w6v5u4t3s2...
[10:23:47] [INFO ] Listening on 192.168.1.10:51234
[10:23:47] [INFO ] TCP server started on 192.168.1.10:51234
[10:23:47] [INFO ] Publishing service 'TAZCOM Node x9y8z7w6._tazcom._tcp.local.'
[10:23:48] [INFO ] Peer Discovered: a1b2c3d4e5f6g7h8... @ 192.168.1.10:54321
[10:23:48] [INFO ] Sent HELLO to a1b2c3d4e5f6g7h8... @ 192.168.1.10:54321
[10:23:48] [INFO ] Received ACK from a1b2c3d4e5f6g7h8...
```

### Step 4: Start Node #3 (Optional)
```bash
# Terminal 3
python poc-02_connection.py
```

Node #3 will:
1. Discover Nodes #1 and #2
2. Send HELLO to both
3. Receive ACK from both

---

## Complete Event Sequence

Here's what happens when Node B discovers Node A:

```
Timeline:
---------

[T+0s] Node A starts
  - Generates identity: a1b2c3d4...
  - Starts TCP server on 192.168.1.10:54321
  - Publishes Zeroconf service _tazcom._tcp.local.

[T+2s] Node B starts
  - Generates identity: x9y8z7w6...
  - Starts TCP server on 192.168.1.10:51234
  - Publishes Zeroconf service _tazcom._tcp.local.

[T+3s] Node B discovers Node A's Zeroconf service
  - _on_service_added() callback triggered
  - Peer added to self.peers: {
      "a1b2c3d4...": {
        "ip": "192.168.1.10",
        "port": "54321",
        "name": "TAZCOM Node a1b2c3d4._tazcom._tcp.local."
      }
    }
  - send_hello("a1b2c3d4...") called asynchronously

[T+3.1s] Node B establishes TCP connection to Node A
  - Node A's TCP server accepts connection via handle_connection()
  - Node B sends: {"type":"HELLO","from":"x9y8z7w6..."}\n

[T+3.15s] Node A's handle_connection() receives the message
  - Logs: "Message from ('192.168.1.10', 51234): {"type":"HELLO","from":"x9y8z7w6..."}"
  - Sends back: ACK\n
  - Closes connection

[T+3.2s] Node B receives ACK response
  - Logs: "Received ACK from x9y8z7w6..."
  - Closes connection
```

---

## Data Flow Diagram

```
┌─────────────────┐                    ┌─────────────────┐
│    Node A       │                    │    Node B       │
│  192.168.1.10   │                    │  192.168.1.10   │
│    Port 54321   │                    │   Port 51234    │
└────────┬────────┘                    └────────┬────────┘
         │                                       │
         │         1. Zeroconf Discovery        │
         │◄─────────────────────────────────────│
         │         (Multicast on LAN)            │
         │                                       │
         │ 2. TCP Connection (Port 54321)       │
         │◄─────────────────────────────────────│
         │                                       │
         │         3. HELLO Message             │
         │◄─────────────────────────────────────│
         │  {"type":"HELLO","from":"..."}       │
         │                                       │
         │ 4. ACK Response                      │
         │─────────────────────────────────────►│
         │  ACK                                  │
         │                                       │
         │         5. Connection Closed         │
         │─────────────────────────────────────►│
         │                                       │
```

---

## Error Handling

The implementation includes graceful error handling for:

### **Connection Refused**
```
[10:23:52] [WARNING] Connection refused by x9y8z7w6... @ 192.168.1.11:51234
```
→ Peer's TCP server may not be running yet. Node will retry when the peer is discovered again.

### **Connection Timeout**
```
[10:23:55] [WARNING] Connection timeout to x9y8z7w6... @ 192.168.1.11:51234
```
→ Network delay or peer is unreachable. The node logs the issue and continues.

### **Message Size Exceeded**
```
[10:23:58] [WARNING] Message from ('192.168.1.11', 51234) exceeds size limit
```
→ Server rejects messages larger than 1024 bytes. Can be adjusted via `MESSAGE_SIZE_LIMIT`.

### **Unexpected Errors**
```
[10:24:00] [WARNING] Error communicating with x9y8z7w6...: [details]
```
→ Caught by the try-except in `send_hello()`. The node continues operating normally.

---

## Code Architecture

### Key Classes & Methods

| Component | Purpose |
|-----------|---------|
| `TAZCOMNode.handle_connection()` | TCP server handler for incoming messages |
| `TAZCOMNode._start_tcp_server()` | Initializes the asyncio TCP server |
| `TAZCOMNode.send_hello()` | Client method to send messages to peers |
| `TAZCOMNode._on_service_added()` | **ENHANCED**: Now calls `send_hello()` |
| `TAZCOMNode.shutdown()` | **ENHANCED**: Now closes TCP server |

### Message Protocol Constants

```python
MESSAGE_ENCODING = "utf-8"          # All messages are UTF-8 encoded
MESSAGE_TERMINATOR = b"\n"          # Newline delimited
MESSAGE_SIZE_LIMIT = 1024           # 1KB max message size
```

---

## Threading & Concurrency Model

```
Main asyncio Event Loop
│
├─ _start_tcp_server()
│  └─ handle_connection() [for each incoming connection]
│
├─ Zeroconf ServiceBrowser [runs in separate thread]
│  └─ _on_service_state_change() [callback, called in Zeroconf thread]
│     └─ run_coroutine_threadsafe()
│        └─ _on_service_added() [scheduled in event loop]
│           └─ send_hello() [async, runs in event loop]
│
└─ run() [main loop]
   └─ asyncio.sleep(1)
```

**Key Point:** The Zeroconf callbacks run in a separate thread, but all state modifications are properly marshaled into the asyncio event loop using `run_coroutine_threadsafe()` and `asyncio.Lock`.

---

## Shutting Down

Press `Ctrl+C` to gracefully shut down:

```bash
^C
[10:24:15] [INFO ] Shutdown signal received...
[10:24:15] [INFO ] TCP server closed
[10:24:15] [INFO ] Zeroconf service unregistered
[10:24:15] [INFO ] Node shut down successfully.
```

The node will:
1. Close all TCP connections
2. Unregister from Zeroconf
3. Clean up resources
4. Exit cleanly

---

## Next Steps

This PoC demonstrates the core P2P communication pattern. Future enhancements:

- **poc-03_chat_basic:** Implement a full TUI chat interface
- **Message Types:** Extend from simple HELLO to support multiple message types
- **Message Routing:** Implement gossip protocol for multi-hop message delivery
- **Authentication:** Sign messages with Ed25519 keys for authenticity verification
- **Encryption:** Encrypt message payloads for privacy

---

## Troubleshooting

### "Connection refused" on startup
This is normal! Nodes may discover each other before their servers are fully ready. The error is logged and doesn't break anything.

### Port already in use
If the script fails to bind to the random port, check if another TAZCOM instance is running on your machine.

### Peers not discovered
Ensure all nodes are on the same local network (Wi-Fi or wired). Zeroconf requires multicast, which may be blocked by:
- Network segmentation/VLANs
- Multicast-blocking firewall rules
- Nodes on different subnets

### Messages not received
Check that the TCP server is running (`[INFO] TCP server started...` in logs). If a node crashes, peer connections will fail. Restart the node to recover.

---

## Implementation Quality Checklist

✅ Asynchronous TCP server using `asyncio.start_server()`
✅ Asynchronous TCP client using `asyncio.open_connection()`
✅ Thread-safe peer access with `asyncio.Lock`
✅ Proper error handling for network operations
✅ Graceful shutdown of server and resources
✅ JSON message serialization
✅ Logging for all significant events
✅ Type hints throughout
✅ Self-contained, single-file implementation

---

## Performance Notes

- Each connection is handled independently; no connection pooling
- Message size limited to 1024 bytes for safety
- Nodes can handle multiple concurrent connections (one per peer)
- No message buffering; each message is read/written in a single operation

This is appropriate for PoC. Future versions may add:
- Connection pooling
- Message buffering for larger payloads
- Rate limiting
- Timeout tuning
