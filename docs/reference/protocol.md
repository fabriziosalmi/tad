# Protocol Specification

TAD protocol specification and message formats.

## Overview

TAD uses a custom peer-to-peer protocol built on WebSockets for real-time communication. The protocol is designed for:
- Decentralized operation (no central server)
- Offline-first capability
- End-to-end encryption support
- Gossip-based message propagation

## Protocol Stack

```
┌─────────────────────────────────────┐
│   Application Layer (TAD Logic)    │
├─────────────────────────────────────┤
│   Message Layer (JSON Messages)    │
├─────────────────────────────────────┤
│   Transport Layer (WebSocket)      │
├─────────────────────────────────────┤
│   Network Layer (TCP/IP)           │
└─────────────────────────────────────┘
```

## Transport

### WebSocket Connection

- **Protocol:** WebSocket (RFC 6455)
- **Default Port:** 8765
- **Endpoint:** `ws://<ip>:<port>/tad`

### Connection Handshake

```
Client → Server: WebSocket Upgrade Request
Server → Client: Upgrade Response (101 Switching Protocols)
Client → Server: HELLO message
Server → Client: WELCOME message
```

### HELLO Message

Sent by client after WebSocket connection:

```json
{
  "type": "hello",
  "version": "1.0",
  "node_id": "abcd1234efgh5678ijkl90mnopqrstuv",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "timestamp": 1701187800.123,
  "capabilities": ["gossip", "encryption", "channels"]
}
```

### WELCOME Message

Server response to HELLO:

```json
{
  "type": "welcome",
  "version": "1.0",
  "node_id": "wxyz9876stuv5432ponm1098lkji6543",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "timestamp": 1701187801.456,
  "peers": [
    {"node_id": "peer1...", "address": "192.168.1.100:8765"},
    {"node_id": "peer2...", "address": "192.168.1.101:8765"}
  ]
}
```

## Message Types

### 1. Chat Message

```json
{
  "type": "message",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": 1701187800.123,
  "sender_id": "abcd1234...",
  "sender_name": "Alice",
  "channel": "#general",
  "content": "Hello, world!",
  "signature": "base64_encoded_signature"
}
```

### 2. Gossip Message

See [Gossip Protocol API](/reference/api-gossip) for details.

```json
{
  "type": "gossip",
  "version": "1.0",
  "message": {
    "id": "uuid",
    "timestamp": 1701187800.123,
    "sender_id": "node_id",
    "channel": "#general",
    "content": "message",
    "ttl": 5,
    "hop_count": 0
  }
}
```

### 3. Channel Control

#### CREATE_CHANNEL

```json
{
  "type": "create_channel",
  "channel": "#newchannel",
  "encrypted": false,
  "timestamp": 1701187800.123
}
```

#### JOIN_CHANNEL

```json
{
  "type": "join_channel",
  "channel": "#general",
  "timestamp": 1701187800.123
}
```

#### LEAVE_CHANNEL

```json
{
  "type": "leave_channel",
  "channel": "#random",
  "timestamp": 1701187800.123
}
```

### 4. Peer Discovery

#### PEER_ANNOUNCE

```json
{
  "type": "peer_announce",
  "node_id": "abcd1234...",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...",
  "address": "192.168.1.100:8765",
  "timestamp": 1701187800.123,
  "channels": ["#general", "#dev"]
}
```

#### PEER_REQUEST

```json
{
  "type": "peer_request",
  "timestamp": 1701187800.123
}
```

#### PEER_RESPONSE

```json
{
  "type": "peer_response",
  "peers": [
    {
      "node_id": "peer1...",
      "address": "192.168.1.100:8765",
      "last_seen": 1701187800.123
    }
  ],
  "timestamp": 1701187801.123
}
```

### 5. Sync Messages

#### SYNC_REQUEST

Request message history:

```json
{
  "type": "sync_request",
  "channel": "#general",
  "since": 1701180000.0,
  "limit": 100
}
```

#### SYNC_RESPONSE

```json
{
  "type": "sync_response",
  "channel": "#general",
  "messages": [
    {
      "id": "uuid",
      "timestamp": 1701187800.123,
      "sender_id": "node_id",
      "content": "message"
    }
  ],
  "has_more": false
}
```

### 6. Control Messages

#### PING

```json
{
  "type": "ping",
  "timestamp": 1701187800.123
}
```

#### PONG

```json
{
  "type": "pong",
  "timestamp": 1701187801.123
}
```

#### ERROR

```json
{
  "type": "error",
  "code": "INVALID_SIGNATURE",
  "message": "Message signature verification failed",
  "timestamp": 1701187800.123
}
```

## Message Signing

All messages include Ed25519 signatures:

### Signature Generation

```python
import json
from cryptography.hazmat.primitives.asymmetric import ed25519

# Create canonical message (without signature field)
message_data = {
    "type": "message",
    "id": "uuid",
    "timestamp": 1701187800.123,
    "sender_id": "node_id",
    "content": "Hello"
}

# Canonicalize (sorted keys, no whitespace)
canonical = json.dumps(message_data, sort_keys=True, separators=(',', ':'))

# Sign
signature = private_key.sign(canonical.encode('utf-8'))

# Add signature to message
message_data["signature"] = base64.b64encode(signature).decode('ascii')
```

### Signature Verification

```python
# Extract signature
signature = base64.b64decode(message["signature"])

# Remove signature from message
message_copy = {k: v for k, v in message.items() if k != "signature"}

# Canonicalize
canonical = json.dumps(message_copy, sort_keys=True, separators=(',', ':'))

# Verify
try:
    public_key.verify(signature, canonical.encode('utf-8'))
    print("Valid signature")
except InvalidSignature:
    print("Invalid signature")
```

## Encrypted Messages

For private channels:

```json
{
  "type": "message",
  "id": "uuid",
  "timestamp": 1701187800.123,
  "sender_id": "node_id",
  "channel": "#secret",
  "encrypted": true,
  "nonce": "base64_nonce",
  "ciphertext": "base64_encrypted_content",
  "tag": "base64_auth_tag",
  "signature": "base64_outer_signature"
}
```

See [Cryptography](/reference/cryptography) for encryption details.

## Error Codes

| Code | Description | Action |
|------|-------------|--------|
| `INVALID_FORMAT` | Malformed JSON | Drop message |
| `INVALID_SIGNATURE` | Signature verification failed | Drop message |
| `UNKNOWN_SENDER` | Sender not in peer list | Request peer info |
| `CHANNEL_NOT_FOUND` | Channel doesn't exist | Create or ignore |
| `PERMISSION_DENIED` | Not authorized | Drop message |
| `RATE_LIMITED` | Too many messages | Slow down |
| `MESSAGE_TOO_LARGE` | Exceeds size limit | Split or reject |
| `PROTOCOL_VERSION_MISMATCH` | Incompatible version | Upgrade or disconnect |

## Protocol Versioning

**Current Version:** 1.0

### Version Negotiation

```json
{
  "type": "hello",
  "version": "1.0",
  "supported_versions": ["1.0", "0.9"]
}
```

Server responds with highest mutually supported version.

### Compatibility Matrix

| Client | Server 1.0 | Server 0.9 |
|--------|-----------|-----------|
| 1.0    | ✅ Full    | ⚠️ Limited |
| 0.9    | ⚠️ Limited | ✅ Full    |

## Rate Limiting

### Per-Peer Limits

```python
RATE_LIMITS = {
    "messages": 10,      # per second
    "gossip": 50,        # per second
    "sync_requests": 5,  # per minute
    "peer_requests": 10  # per minute
}
```

### Backoff Strategy

```python
def calculate_backoff(attempt):
    """Exponential backoff with jitter"""
    base_delay = 1.0  # seconds
    max_delay = 60.0  # seconds
    
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    
    return delay + jitter
```

## Connection Management

### Heartbeat

```python
HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 90   # seconds (3 missed)

# Send PING every 30 seconds
# Disconnect if no PONG within 90 seconds
```

### Reconnection

```python
RECONNECT_ATTEMPTS = 5
RECONNECT_BACKOFF = [1, 2, 5, 10, 30]  # seconds
```

## Best Practices

### For Clients

1. **Always verify signatures**
2. **Validate message format** before processing
3. **Implement rate limiting** to avoid bans
4. **Cache peer list** for offline operation
5. **Handle errors gracefully**

### For Developers

1. **Use canonical JSON** for signing
2. **Implement proper timeout handling**
3. **Log protocol violations**
4. **Version all messages**
5. **Test with network delays**

## Security Considerations

### Message Authentication

- All messages MUST be signed
- Signatures MUST be verified before processing
- Invalid signatures MUST be dropped immediately

### Rate Limiting

- Implement per-peer rate limits
- Use token bucket or leaky bucket algorithms
- Ban peers exceeding limits

### Message Size Limits

```python
MAX_MESSAGE_SIZE = 64 * 1024  # 64 KB
MAX_CONTENT_LENGTH = 32 * 1024  # 32 KB
```

### Timestamp Validation

```python
def validate_timestamp(timestamp):
    """Reject messages with invalid timestamps"""
    now = time.time()
    
    # Reject future messages (allow 60s clock skew)
    if timestamp > now + 60:
        return False
    
    # Reject very old messages (24 hours)
    if timestamp < now - 86400:
        return False
    
    return True
```

## Testing

### Protocol Compliance

```python
def test_message_format():
    """Test message conforms to protocol"""
    message = create_message("Hello")
    
    assert message["type"] == "message"
    assert "id" in message
    assert "timestamp" in message
    assert "signature" in message
    assert verify_signature(message)
```

### Network Simulation

```bash
# Test with network delay
tc qdisc add dev lo root netem delay 100ms

# Test with packet loss
tc qdisc add dev lo root netem loss 10%

# Test with bandwidth limit
tc qdisc add dev lo root tbf rate 1mbit burst 32kbit latency 400ms
```

## See Also

- [Gossip Protocol](/reference/api-gossip) - Message propagation
- [Cryptography](/reference/cryptography) - Encryption details
- [Architecture](/reference/architecture) - System design
