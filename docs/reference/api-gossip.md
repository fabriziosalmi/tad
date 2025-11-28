# Gossip Protocol API

Technical reference for TAD's gossip-based message propagation protocol.

## Overview

TAD uses a **gossip protocol** (also known as epidemic protocol) to propagate messages across the peer-to-peer network. This ensures reliable message delivery without requiring a central server.

## How Gossip Works

### Basic Concept

1. Node A sends a message
2. A forwards to 3 random peers (fanout)
3. Each peer forwards to 3 more peers
4. Process continues until TTL expires
5. Duplicate detection prevents loops

```
     A
    /|\
   B C D
  /|\ ...
 E F G
```

### Message Flow

```
User sends message
       ↓
Create message packet
       ↓
Sign message
       ↓
Store in local DB
       ↓
Add to gossip queue
       ↓
Select N random peers (fanout)
       ↓
Forward to selected peers
       ↓
Track in seen cache
```

## Protocol Specification

### Message Format

```json
{
  "type": "gossip",
  "version": "1.0",
  "message": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": 1701187800.123,
    "sender_id": "abcd1234efgh5678ijkl90mnopqrstuv",
    "sender_name": "Alice",
    "channel": "#general",
    "content": "Hello, world!",
    "signature": "base64_encoded_signature",
    "ttl": 5,
    "hop_count": 0
  }
}
```

### Message Fields

| Field | Type | Description |
|-------|------|-------------|
| `type` | string | Always "gossip" |
| `version` | string | Protocol version |
| `message.id` | UUID | Unique message identifier |
| `message.timestamp` | float | Unix timestamp |
| `message.sender_id` | string | Node ID of original sender |
| `message.sender_name` | string | Display name |
| `message.channel` | string | Target channel |
| `message.content` | string | Message content |
| `message.signature` | string | Ed25519 signature (base64) |
| `message.ttl` | integer | Time-to-live (hops remaining) |
| `message.hop_count` | integer | Number of hops so far |

## API Reference

### GossipProtocol Class

```python
from tad.network.gossip import GossipProtocol

class GossipProtocol:
    def __init__(self, node, fanout=3, ttl=5, cache_size=10000):
        """
        Initialize gossip protocol.
        
        Args:
            node: TADNode instance
            fanout: Number of peers to forward to
            ttl: Maximum hops for message
            cache_size: Size of seen messages cache
        """
```

### Broadcasting Messages

```python
def broadcast_message(self, channel: str, content: str) -> str:
    """
    Broadcast message to channel via gossip.
    
    Args:
        channel: Channel name (e.g., "#general")
        content: Message content
        
    Returns:
        message_id: UUID of created message
        
    Raises:
        ValueError: If channel name invalid
        NetworkError: If no peers available
    """
    message_id = str(uuid.uuid4())
    
    # Create message packet
    message = {
        "id": message_id,
        "timestamp": time.time(),
        "sender_id": self.node.node_id,
        "sender_name": self.node.display_name,
        "channel": channel,
        "content": content,
        "signature": self._sign_message(content),
        "ttl": self.ttl,
        "hop_count": 0
    }
    
    # Store locally
    self.node.db.store_message(message)
    
    # Add to seen cache
    self._add_to_cache(message_id)
    
    # Gossip to peers
    self._gossip(message)
    
    return message_id
```

### Receiving Messages

```python
def receive_message(self, message: dict, from_peer: str) -> bool:
    """
    Receive and process gossip message.
    
    Args:
        message: Message packet
        from_peer: Peer ID who sent message
        
    Returns:
        bool: True if message was new and processed
        
    Raises:
        InvalidSignature: If signature verification fails
    """
    message_id = message["id"]
    
    # Check if already seen
    if self._is_seen(message_id):
        return False
    
    # Verify signature
    if not self._verify_signature(message):
        raise InvalidSignature("Invalid message signature")
    
    # Check TTL
    if message["ttl"] <= 0:
        return False
    
    # Store message
    self.node.db.store_message(message)
    
    # Add to seen cache
    self._add_to_cache(message_id)
    
    # Forward to other peers
    message["ttl"] -= 1
    message["hop_count"] += 1
    self._gossip(message, exclude=[from_peer])
    
    return True
```

### Forwarding Messages

```python
def _gossip(self, message: dict, exclude: list = None) -> int:
    """
    Forward message to random peers.
    
    Args:
        message: Message to forward
        exclude: Peer IDs to exclude from forwarding
        
    Returns:
        int: Number of peers forwarded to
    """
    exclude = exclude or []
    
    # Get available peers
    available_peers = [
        p for p in self.node.get_connected_peers()
        if p.peer_id not in exclude
    ]
    
    # Select random subset (fanout)
    import random
    selected = random.sample(
        available_peers,
        min(self.fanout, len(available_peers))
    )
    
    # Forward to selected peers
    count = 0
    for peer in selected:
        try:
            peer.send_message({
                "type": "gossip",
                "version": "1.0",
                "message": message
            })
            count += 1
        except Exception as e:
            print(f"Failed to forward to {peer.peer_id}: {e}")
    
    return count
```

### Duplicate Detection

```python
def _is_seen(self, message_id: str) -> bool:
    """Check if message has been seen before."""
    return message_id in self.seen_cache

def _add_to_cache(self, message_id: str):
    """Add message to seen cache."""
    # Add to cache
    self.seen_cache[message_id] = time.time()
    
    # Prune old entries
    if len(self.seen_cache) > self.cache_size:
        self._prune_cache()

def _prune_cache(self):
    """Remove old entries from seen cache."""
    cutoff = time.time() - 3600  # 1 hour
    self.seen_cache = {
        msg_id: ts for msg_id, ts in self.seen_cache.items()
        if ts > cutoff
    }
```

## Configuration

### Parameters

```python
GOSSIP_CONFIG = {
    # Forwarding
    "fanout": 3,              # Peers to forward to
    "ttl": 5,                 # Maximum hops
    "interval": 1.0,          # Gossip interval (seconds)
    
    # Caching
    "cache_size": 10000,      # Seen messages cache size
    "cache_ttl": 3600,        # Cache entry lifetime (seconds)
    
    # Retransmission
    "retry_count": 3,         # Retries on failure
    "retry_delay": 1.0,       # Delay between retries (seconds)
    
    # Limits
    "max_message_size": 65536,  # Maximum message size (bytes)
    "rate_limit": 10,           # Messages per second
}
```

### Tuning Guidelines

#### High-Throughput Network
```python
config = {
    "fanout": 5,      # More redundancy
    "ttl": 7,         # Wider spread
    "interval": 0.5,  # Faster propagation
}
```

#### Low-Bandwidth Network
```python
config = {
    "fanout": 2,      # Less redundancy
    "ttl": 4,         # Limit spread
    "interval": 2.0,  # Slower propagation
}
```

#### Large Network (100+ nodes)
```python
config = {
    "fanout": 4,
    "ttl": 6,
    "cache_size": 50000,
}
```

## Performance Analysis

### Message Complexity

**Time Complexity:**
- Broadcast: O(1) - constant time to initiate
- Receive: O(1) - constant time to process
- Propagation: O(log N) - logarithmic with network size

**Space Complexity:**
- Memory: O(M) where M = cache size
- Network: O(F × N) where F = fanout, N = nodes

### Propagation Speed

With fanout=3, TTL=5:

| Hop | Nodes Reached | Cumulative |
|-----|---------------|------------|
| 0   | 1             | 1          |
| 1   | 3             | 4          |
| 2   | 9             | 13         |
| 3   | 27            | 40         |
| 4   | 81            | 121        |
| 5   | 243           | 364        |

**Theoretical reach:** 3^TTL nodes

### Network Overhead

Messages sent per broadcast:
```
Total = 1 + fanout × (1 + fanout × (1 + ... ))
      = (fanout^(TTL+1) - 1) / (fanout - 1)
```

Example (fanout=3, TTL=5):
```
Total = (3^6 - 1) / 2 = 364 messages
```

**Efficiency:** Trade-off between reliability and bandwidth

## Reliability

### Message Delivery

Probability of message reaching all nodes:

```
P(reach) ≈ 1 - (1 - P(peer))^fanout
```

Where P(peer) = probability peer is online

Example:
- 90% peer availability
- Fanout = 3
- P(reach) ≈ 1 - 0.1^3 = 99.9%

### Fault Tolerance

Gossip protocol is resilient to:
- ✅ **Node failures** - Multiple paths available
- ✅ **Network partitions** - Messages spread within partition
- ✅ **Message loss** - Redundant forwarding
- ❌ **Byzantine failures** - Malicious nodes can disrupt

### Attack Resistance

| Attack | Impact | Mitigation |
|--------|--------|------------|
| Message spam | High bandwidth | Rate limiting, peer reputation |
| Duplicate injection | Cache overflow | Signature verification, TTL limits |
| Selective forwarding | Reduced reach | Multiple paths, monitoring |
| Sybil attack | Network pollution | Peer limits, allowlists |

## Monitoring

### Metrics

```python
class GossipMetrics:
    def __init__(self):
        self.messages_sent = 0
        self.messages_received = 0
        self.duplicates_dropped = 0
        self.ttl_expired = 0
        self.forwarding_errors = 0
        
    def get_stats(self):
        return {
            "sent": self.messages_sent,
            "received": self.messages_received,
            "duplicates": self.duplicates_dropped,
            "expired": self.ttl_expired,
            "errors": self.forwarding_errors,
            "cache_size": len(self.seen_cache),
        }
```

### Debugging

```python
# Enable gossip debug logging
import logging
logging.getLogger('tad.network.gossip').setLevel(logging.DEBUG)

# Trace message propagation
def trace_message(message_id):
    """Trace path of message through network"""
    hops = db.query(
        "SELECT hop_count, peer_id, timestamp FROM message_log "
        "WHERE message_id = ? ORDER BY timestamp",
        (message_id,)
    )
    
    for hop in hops:
        print(f"Hop {hop['hop_count']}: {hop['peer_id']} at {hop['timestamp']}")
```

## Best Practices

### For Developers

1. **Always verify signatures**
   ```python
   if not verify_signature(message):
       return  # Drop invalid messages
   ```

2. **Implement backpressure**
   ```python
   if len(gossip_queue) > MAX_QUEUE:
       time.sleep(0.1)  # Slow down
   ```

3. **Monitor cache size**
   ```python
   if len(seen_cache) > cache_size:
       prune_cache()
   ```

### For Network Operators

1. **Tune fanout based on network size**
   - Small (< 10 nodes): fanout = 2
   - Medium (10-50 nodes): fanout = 3
   - Large (50+ nodes): fanout = 4-5

2. **Adjust TTL for network diameter**
   - TTL should be 2× network diameter
   - Monitor hop counts to determine optimal TTL

3. **Rate limit aggressively**
   - Prevent spam and DoS
   - Implement per-peer limits

## See Also

- [Architecture](/reference/architecture) - System design
- [Protocol](/reference/protocol) - Protocol overview
- [Network Configuration](/guide/networking) - Network setup
