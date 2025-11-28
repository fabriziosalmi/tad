# Database API

API reference for TAD's database persistence layer.

## Overview

The Database API provides a clean interface for storing and retrieving TAD data. It abstracts SQLite operations and handles:
- Message storage and retrieval
- Channel management
- Peer tracking
- Configuration storage

## Database Class

```python
from tad.persistence.database import Database

db = Database(path="tad_data/tad.db")
```

### Initialization

```python
def __init__(self, path: str = "tad_data/tad.db"):
    """
    Initialize database connection.
    
    Args:
        path: Path to SQLite database file
        
    Raises:
        DatabaseError: If database cannot be opened
    """
```

### Schema Setup

```python
def init_schema(self):
    """
    Create database tables if they don't exist.
    
    Creates:
        - messages table
        - channels table
        - peers table
        - channel_members table
        - gossip_cache table
        - config table
    """
```

## Message Operations

### Store Message

```python
def store_message(
    self,
    message_id: str,
    timestamp: float,
    sender_id: str,
    sender_name: str,
    channel: str,
    content: str,
    encrypted: bool = False,
    signature: str = None,
    nonce: str = None
) -> bool:
    """
    Store a message in the database.
    
    Args:
        message_id: Unique message identifier (UUID)
        timestamp: Unix timestamp
        sender_id: Node ID of sender
        sender_name: Display name of sender
        channel: Channel name (e.g., "#general")
        content: Message content (plain or encrypted)
        encrypted: Whether message is encrypted
        signature: Ed25519 signature (base64)
        nonce: Encryption nonce (base64, if encrypted)
        
    Returns:
        bool: True if stored successfully
        
    Raises:
        DatabaseError: If storage fails
        
    Example:
        >>> db.store_message(
        ...     message_id="550e8400-e29b-41d4-a716-446655440000",
        ...     timestamp=1701187800.123,
        ...     sender_id="abc123...",
        ...     sender_name="Alice",
        ...     channel="#general",
        ...     content="Hello, world!",
        ...     signature="base64_sig..."
        ... )
        True
    """
```

### Get Messages

```python
def get_messages(
    self,
    channel: str,
    limit: int = 100,
    offset: int = 0,
    since: float = None
) -> List[Dict]:
    """
    Retrieve messages from a channel.
    
    Args:
        channel: Channel name
        limit: Maximum number of messages to return
        offset: Number of messages to skip
        since: Only return messages after this timestamp
        
    Returns:
        List of message dictionaries, ordered by timestamp DESC
        
    Example:
        >>> messages = db.get_messages("#general", limit=50)
        >>> for msg in messages:
        ...     print(f"{msg['sender_name']}: {msg['content']}")
    """
```

### Get Message by ID

```python
def get_message(self, message_id: str) -> Dict:
    """
    Get a specific message by ID.
    
    Args:
        message_id: Message UUID
        
    Returns:
        Message dictionary or None if not found
    """
```

### Delete Messages

```python
def delete_messages(
    self,
    channel: str = None,
    before: float = None
) -> int:
    """
    Delete messages from database.
    
    Args:
        channel: Delete from specific channel (all if None)
        before: Delete messages before this timestamp (all if None)
        
    Returns:
        Number of messages deleted
        
    Example:
        >>> # Delete old messages from #general
        >>> cutoff = time.time() - (30 * 86400)  # 30 days ago
        >>> deleted = db.delete_messages("#general", before=cutoff)
        >>> print(f"Deleted {deleted} old messages")
    """
```

### Search Messages

```python
def search_messages(
    self,
    query: str,
    channel: str = None,
    limit: int = 100
) -> List[Dict]:
    """
    Search for messages containing text.
    
    Args:
        query: Search query string
        channel: Limit to specific channel (all if None)
        limit: Maximum results to return
        
    Returns:
        List of matching messages
        
    Example:
        >>> results = db.search_messages("roadmap", channel="#dev")
        >>> print(f"Found {len(results)} messages")
    """
```

## Channel Operations

### Create Channel

```python
def create_channel(
    self,
    name: str,
    encrypted: bool = False,
    password_hash: str = None,
    salt: bytes = None
) -> bool:
    """
    Create a new channel.
    
    Args:
        name: Channel name (e.g., "#general")
        encrypted: Whether channel is encrypted
        password_hash: Argon2 hash of password (if encrypted)
        salt: Random salt for key derivation (if encrypted)
        
    Returns:
        bool: True if created successfully
        
    Example:
        >>> db.create_channel("#team", encrypted=False)
        True
    """
```

### Get Channel

```python
def get_channel(self, name: str) -> Dict:
    """
    Get channel information.
    
    Args:
        name: Channel name
        
    Returns:
        Channel dictionary or None if not found
        
    Example:
        >>> channel = db.get_channel("#general")
        >>> print(f"Created: {channel['created_at']}")
        >>> print(f"Messages: {channel['message_count']}")
    """
```

### List Channels

```python
def list_channels(self) -> List[Dict]:
    """
    Get all channels.
    
    Returns:
        List of channel dictionaries
        
    Example:
        >>> channels = db.list_channels()
        >>> for ch in channels:
        ...     print(f"{ch['name']}: {ch['message_count']} messages")
    """
```

### Update Channel Activity

```python
def update_channel_activity(self, name: str, timestamp: float = None):
    """
    Update channel's last activity timestamp.
    
    Args:
        name: Channel name
        timestamp: Activity timestamp (current time if None)
    """
```

### Delete Channel

```python
def delete_channel(self, name: str) -> bool:
    """
    Delete a channel and all its messages.
    
    Args:
        name: Channel name
        
    Returns:
        bool: True if deleted successfully
        
    Warning:
        This permanently deletes all channel messages!
    """
```

## Peer Operations

### Store Peer

```python
def store_peer(
    self,
    peer_id: str,
    public_key: str,
    display_name: str = None,
    ip_address: str = None,
    port: int = None
) -> bool:
    """
    Store or update peer information.
    
    Args:
        peer_id: Node ID
        public_key: Ed25519 public key (PEM format)
        display_name: Human-readable name
        ip_address: IP address
        port: Port number
        
    Returns:
        bool: True if stored successfully
    """
```

### Get Peer

```python
def get_peer(self, peer_id: str) -> Dict:
    """
    Get peer information.
    
    Args:
        peer_id: Node ID
        
    Returns:
        Peer dictionary or None if not found
    """
```

### List Peers

```python
def list_peers(self, status: str = None) -> List[Dict]:
    """
    Get all known peers.
    
    Args:
        status: Filter by status ('online'/'offline'/None for all)
        
    Returns:
        List of peer dictionaries
        
    Example:
        >>> online_peers = db.list_peers(status='online')
        >>> print(f"{len(online_peers)} peers online")
    """
```

### Update Peer Status

```python
def update_peer_status(
    self,
    peer_id: str,
    status: str,
    timestamp: float = None
):
    """
    Update peer online/offline status.
    
    Args:
        peer_id: Node ID
        status: 'online', 'offline', or 'unknown'
        timestamp: Last seen timestamp (current if None)
    """
```

### Block/Unblock Peer

```python
def block_peer(self, peer_id: str) -> bool:
    """Block a peer."""
    
def unblock_peer(self, peer_id: str) -> bool:
    """Unblock a peer."""
    
def is_peer_blocked(self, peer_id: str) -> bool:
    """Check if peer is blocked."""
```

## Channel Membership

### Join Channel

```python
def join_channel(self, channel: str, peer_id: str) -> bool:
    """
    Add peer to channel.
    
    Args:
        channel: Channel name
        peer_id: Node ID
        
    Returns:
        bool: True if joined successfully
    """
```

### Leave Channel

```python
def leave_channel(self, channel: str, peer_id: str) -> bool:
    """
    Remove peer from channel.
    
    Args:
        channel: Channel name
        peer_id: Node ID
        
    Returns:
        bool: True if left successfully
    """
```

### Get Channel Members

```python
def get_channel_members(self, channel: str) -> List[str]:
    """
    Get list of peer IDs in channel.
    
    Args:
        channel: Channel name
        
    Returns:
        List of peer IDs
    """
```

### Get Peer Channels

```python
def get_peer_channels(self, peer_id: str) -> List[str]:
    """
    Get channels a peer is in.
    
    Args:
        peer_id: Node ID
        
    Returns:
        List of channel names
    """
```

## Gossip Cache

### Add to Cache

```python
def add_to_gossip_cache(self, message_id: str, ttl: int = 5) -> bool:
    """
    Mark message as seen to prevent duplicates.
    
    Args:
        message_id: Message UUID
        ttl: Time-to-live (hops remaining)
        
    Returns:
        bool: True if added (False if already seen)
    """
```

### Check Cache

```python
def is_in_gossip_cache(self, message_id: str) -> bool:
    """
    Check if message has been seen before.
    
    Args:
        message_id: Message UUID
        
    Returns:
        bool: True if message is in cache
    """
```

### Clean Cache

```python
def clean_gossip_cache(self, max_age: float = 3600):
    """
    Remove old entries from gossip cache.
    
    Args:
        max_age: Maximum age in seconds (default 1 hour)
    """
```

## Configuration

### Get Config

```python
def get_config(self, key: str, default: Any = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        
    Returns:
        Configuration value
        
    Example:
        >>> node_id = db.get_config('node_id')
        >>> max_peers = db.get_config('max_peers', default=100)
    """
```

### Set Config

```python
def set_config(self, key: str, value: Any):
    """
    Set configuration value.
    
    Args:
        key: Configuration key
        value: Value to store (will be converted to string)
    """
```

## Utility Methods

### Vacuum

```python
def vacuum(self):
    """
    Optimize database and reclaim space.
    
    Should be run periodically or after large deletions.
    """
```

### Get Statistics

```python
def get_statistics(self) -> Dict:
    """
    Get database statistics.
    
    Returns:
        Dictionary with statistics:
        - total_messages: Total message count
        - total_channels: Total channel count
        - total_peers: Total peer count
        - database_size: Size in bytes
        - oldest_message: Oldest message timestamp
        - newest_message: Newest message timestamp
    """
```

### Close

```python
def close(self):
    """
    Close database connection.
    
    Always call when done using database.
    """
```

## Context Manager Support

```python
# Use as context manager
with Database("tad_data/tad.db") as db:
    db.store_message(...)
    messages = db.get_messages("#general")
# Database automatically closed
```

## Error Handling

```python
from tad.persistence.database import DatabaseError

try:
    db.store_message(...)
except DatabaseError as e:
    print(f"Database error: {e}")
```

## Thread Safety

The Database class is thread-safe. Multiple threads can use the same instance:

```python
import threading

db = Database()

def worker():
    db.store_message(...)

threads = [threading.Thread(target=worker) for _ in range(10)]
for t in threads:
    t.start()
```

## See Also

- [Database Schema](/reference/database) - Database structure
- [Export & Import](/guide/export-import) - Data backup
- [Architecture](/reference/architecture) - System design
