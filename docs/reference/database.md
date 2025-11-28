# Database Schema

TAD's SQLite database structure and persistence layer.

## Overview

TAD uses SQLite for local data persistence with a simple, efficient schema designed for:
- Fast message retrieval
- Efficient peer lookup
- Channel management
- Export/import capability

## Database Location

```
tad_data/
  tad.db           # Main database file
  tad.db-shm       # Shared memory file
  tad.db-wal       # Write-ahead log
```

## Schema

### Messages Table

Stores all chat messages.

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    timestamp REAL NOT NULL,
    sender_id TEXT NOT NULL,
    sender_name TEXT,
    channel TEXT NOT NULL,
    content TEXT NOT NULL,
    encrypted BOOLEAN DEFAULT 0,
    signature TEXT,
    nonce TEXT,
    created_at REAL DEFAULT (julianday('now'))
);

CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_messages_timestamp ON messages(timestamp);
CREATE INDEX idx_messages_sender ON messages(sender_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
```

**Columns:**
- `id`: Unique message identifier (UUID)
- `timestamp`: Unix timestamp of message creation
- `sender_id`: Node ID of sender
- `sender_name`: Display name of sender
- `channel`: Channel name (e.g., "#general")
- `content`: Message content (plaintext or encrypted)
- `encrypted`: Boolean flag for encrypted messages
- `signature`: Ed25519 signature (base64)
- `nonce`: Encryption nonce for encrypted messages (base64)
- `created_at`: Database insertion time (Julian day)

### Channels Table

Stores channel metadata.

```sql
CREATE TABLE channels (
    name TEXT PRIMARY KEY,
    encrypted BOOLEAN DEFAULT 0,
    password_hash TEXT,
    salt BLOB,
    created_at REAL DEFAULT (julianday('now')),
    last_activity REAL,
    message_count INTEGER DEFAULT 0
);

CREATE INDEX idx_channels_last_activity ON channels(last_activity);
```

**Columns:**
- `name`: Channel name (e.g., "#general")
- `encrypted`: Boolean flag for private channels
- `password_hash`: Argon2 hash of channel password (if encrypted)
- `salt`: Random salt for key derivation (16 bytes)
- `created_at`: Channel creation time
- `last_activity`: Timestamp of last message
- `message_count`: Cached count of messages

### Peers Table

Stores known peers and their status.

```sql
CREATE TABLE peers (
    peer_id TEXT PRIMARY KEY,
    public_key TEXT NOT NULL,
    display_name TEXT,
    ip_address TEXT,
    port INTEGER,
    last_seen REAL,
    first_seen REAL DEFAULT (julianday('now')),
    status TEXT DEFAULT 'online',
    blocked BOOLEAN DEFAULT 0
);

CREATE INDEX idx_peers_last_seen ON peers(last_seen);
CREATE INDEX idx_peers_status ON peers(status);
```

**Columns:**
- `peer_id`: Node ID
- `public_key`: Ed25519 public key (PEM format)
- `display_name`: Human-readable name
- `ip_address`: Last known IP address
- `port`: Last known port
- `last_seen`: Last contact timestamp
- `first_seen`: First discovery timestamp
- `status`: Current status (online/offline/unknown)
- `blocked`: Boolean flag for blocked peers

### Channel_Members Table

Maps peers to channels (many-to-many).

```sql
CREATE TABLE channel_members (
    channel TEXT NOT NULL,
    peer_id TEXT NOT NULL,
    joined_at REAL DEFAULT (julianday('now')),
    last_read REAL,
    PRIMARY KEY (channel, peer_id),
    FOREIGN KEY (channel) REFERENCES channels(name) ON DELETE CASCADE,
    FOREIGN KEY (peer_id) REFERENCES peers(peer_id) ON DELETE CASCADE
);

CREATE INDEX idx_channel_members_channel ON channel_members(channel);
CREATE INDEX idx_channel_members_peer ON channel_members(peer_id);
```

**Columns:**
- `channel`: Channel name
- `peer_id`: Node ID
- `joined_at`: When peer joined channel
- `last_read`: Last read message timestamp (for unread count)

### Gossip_Cache Table

Tracks seen messages to prevent duplicates.

```sql
CREATE TABLE gossip_cache (
    message_id TEXT PRIMARY KEY,
    seen_at REAL DEFAULT (julianday('now')),
    ttl INTEGER DEFAULT 5
);

CREATE INDEX idx_gossip_cache_seen_at ON gossip_cache(seen_at);
```

**Columns:**
- `message_id`: Message UUID
- `seen_at`: When message was first seen
- `ttl`: Remaining hops (time-to-live)

**Cleanup:** Messages older than 1 hour are periodically deleted.

### Config Table

Stores configuration key-value pairs.

```sql
CREATE TABLE config (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at REAL DEFAULT (julianday('now'))
);
```

**Example entries:**
```sql
INSERT INTO config (key, value) VALUES
    ('node_id', 'abcd1234...'),
    ('display_name', 'Alice'),
    ('version', '1.0.0'),
    ('last_backup', '2024-11-28');
```

## Queries

### Common Operations

#### Insert Message

```sql
INSERT INTO messages (id, timestamp, sender_id, sender_name, channel, content, signature)
VALUES (?, ?, ?, ?, ?, ?, ?);
```

#### Get Recent Messages

```sql
SELECT * FROM messages
WHERE channel = ?
ORDER BY timestamp DESC
LIMIT 100;
```

#### Get Unread Count

```sql
SELECT COUNT(*) FROM messages m
LEFT JOIN channel_members cm ON m.channel = cm.channel
WHERE m.channel = ?
  AND (cm.last_read IS NULL OR m.timestamp > cm.last_read);
```

#### Update Channel Activity

```sql
UPDATE channels
SET last_activity = ?, message_count = message_count + 1
WHERE name = ?;
```

#### Find Peers in Channel

```sql
SELECT p.* FROM peers p
JOIN channel_members cm ON p.peer_id = cm.peer_id
WHERE cm.channel = ?;
```

## Database Management

### Initialization

```python
from tad.persistence.database import Database

db = Database("tad_data/tad.db")
db.init_schema()
```

### Backup

```sql
-- Create backup
VACUUM INTO 'backup.db';

-- Or use SQLite backup API
.backup tad_backup.db
```

```bash
# Command line backup
sqlite3 tad_data/tad.db ".backup 'tad_backup.db'"

# Or simple copy (when TAD is stopped)
cp tad_data/tad.db tad_backup.db
```

### Vacuum

```sql
-- Reclaim space and optimize
VACUUM;

-- Analyze for query optimization
ANALYZE;
```

### Integrity Check

```sql
-- Check database integrity
PRAGMA integrity_check;

-- Quick check
PRAGMA quick_check;
```

## Performance Optimization

### Indexes

All frequently queried columns have indexes:

```sql
-- Composite index for channel + timestamp queries
CREATE INDEX idx_messages_channel_timestamp 
ON messages(channel, timestamp DESC);

-- Index for peer status queries
CREATE INDEX idx_peers_status_last_seen 
ON peers(status, last_seen DESC);
```

### Write-Ahead Logging (WAL)

Enable WAL mode for better concurrency:

```sql
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
```

Benefits:
- Readers don't block writers
- Writers don't block readers
- Better performance for concurrent access

### Prepared Statements

Use prepared statements to avoid SQL injection and improve performance:

```python
cursor.execute(
    "INSERT INTO messages VALUES (?, ?, ?, ?, ?, ?)",
    (msg_id, timestamp, sender_id, channel, content, signature)
)
```

## Data Types

### Timestamps

All timestamps stored as REAL (Julian day numbers):

```sql
-- Current time
julianday('now')

-- Convert to Unix timestamp
(julianday('now') - 2440587.5) * 86400.0

-- Convert from Unix timestamp  
(? / 86400.0) + 2440587.5
```

### Binary Data

Binary data (salts, nonces) stored as BLOB:

```python
# Store
cursor.execute("INSERT INTO channels (salt) VALUES (?)", 
               (sqlite3.Binary(salt_bytes),))

# Retrieve
salt = bytes(row['salt'])
```

### JSON Data

Complex data can be stored as JSON TEXT:

```sql
-- Store
INSERT INTO config (key, value) 
VALUES ('peers_config', json('{"max": 100, "timeout": 30}'));

-- Query
SELECT json_extract(value, '$.max') FROM config WHERE key = 'peers_config';
```

## Migrations

### Version Tracking

```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at REAL DEFAULT (julianday('now'))
);

INSERT INTO schema_version (version) VALUES (1);
```

### Example Migration

```python
def migrate_v1_to_v2(db):
    """Add display_name column to peers table"""
    
    # Check current version
    version = db.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
    
    if version < 2:
        # Add column
        db.execute("ALTER TABLE peers ADD COLUMN display_name TEXT")
        
        # Update version
        db.execute("INSERT INTO schema_version (version) VALUES (2)")
        db.commit()
```

## Export/Import

### Export to JSON

```python
import json

def export_messages(channel):
    rows = db.execute(
        "SELECT * FROM messages WHERE channel = ? ORDER BY timestamp",
        (channel,)
    ).fetchall()
    
    messages = [dict(row) for row in rows]
    
    with open(f"{channel}_export.json", 'w') as f:
        json.dump(messages, f, indent=2)
```

### Import from JSON

```python
def import_messages(filename):
    with open(filename) as f:
        messages = json.load(f)
    
    for msg in messages:
        db.execute(
            "INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?, ?)",
            (msg['id'], msg['timestamp'], msg['sender_id'], 
             msg['channel'], msg['content'], msg['signature'])
        )
    
    db.commit()
```

## Maintenance

### Cleanup Old Data

```python
def cleanup_old_data(days=30):
    """Remove messages older than specified days"""
    
    cutoff = time.time() - (days * 86400)
    
    db.execute(
        "DELETE FROM messages WHERE timestamp < ?",
        (cutoff,)
    )
    
    db.execute(
        "DELETE FROM gossip_cache WHERE seen_at < julianday('now') - 1"
    )
    
    db.commit()
    db.execute("VACUUM")
```

### Statistics

```sql
-- Database size
SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size();

-- Table sizes
SELECT name, 
       (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as count
FROM sqlite_master m WHERE type='table';

-- Message statistics by channel
SELECT channel, COUNT(*) as count, 
       MIN(timestamp) as first, 
       MAX(timestamp) as last
FROM messages
GROUP BY channel;
```

## Security Considerations

### SQL Injection Prevention

Always use parameterized queries:

```python
# NEVER do this
query = f"SELECT * FROM messages WHERE channel = '{channel}'"  # UNSAFE!

# Always do this
query = "SELECT * FROM messages WHERE channel = ?"
cursor.execute(query, (channel,))
```

### Database Encryption

For encrypted database at rest:

```bash
# Use SQLCipher
pip install sqlcipher3

# Open encrypted database
import sqlcipher3 as sqlite3
conn = sqlite3.connect('tad.db')
conn.execute("PRAGMA key='your-encryption-key'")
```

## Troubleshooting

### Database Locked

```python
# Increase timeout
db.execute("PRAGMA busy_timeout = 30000")  # 30 seconds
```

### Corrupted Database

```bash
# Dump and restore
sqlite3 tad.db .dump > dump.sql
sqlite3 tad_new.db < dump.sql
```

### Performance Issues

```sql
-- Analyze query performance
EXPLAIN QUERY PLAN
SELECT * FROM messages WHERE channel = ? ORDER BY timestamp DESC LIMIT 100;

-- Rebuild indexes
REINDEX;

-- Update statistics
ANALYZE;
```

## See Also

- [Export & Import](/guide/export-import) - Data backup
- [Architecture](/reference/architecture) - System design
- [API Documentation](/reference/api-database) - Database API
