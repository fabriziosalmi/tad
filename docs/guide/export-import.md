# Export & Import

Backup, restore, and migrate your TAD data.

## Overview

TAD provides comprehensive export and import functionality to:
- 📦 Backup conversation history
- 🔄 Migrate between devices
- 📊 Analyze chat data
- 💾 Archive old channels
- 🔀 Share conversation logs

## Exporting Data

### Export Current Channel

```
> /export
[SYSTEM] Exported 150 messages to exports/general_20241128_153045.json
```

### Export Specific Channel

```
> /export #dev
[SYSTEM] Exported 89 messages to exports/dev_20241128_153045.json
```

### Export with Custom Format

```
> /export #general json
> /export #general txt
> /export #general md
> /export #general csv
```

## Export Formats

### JSON (Default)
**Best for:** Reimporting, programmatic processing

```json
{
  "channel": "#general",
  "export_date": "2024-11-28T15:30:45Z",
  "message_count": 150,
  "messages": [
    {
      "id": "msg_001",
      "timestamp": "2024-11-28T10:00:00Z",
      "sender": "peer_abc123",
      "sender_name": "Alice",
      "content": "Hello everyone!",
      "channel": "#general"
    }
  ]
}
```

### Plain Text
**Best for:** Reading, sharing externally

```
TAD Export: #general
Exported: 2024-11-28 15:30:45
Messages: 150

[2024-11-28 10:00:00] Alice: Hello everyone!
[2024-11-28 10:01:23] Bob: Hi Alice!
[2024-11-28 10:05:15] Carol: Good morning!
```

### Markdown
**Best for:** Documentation, viewing in editors

```markdown
# TAD Export: #general

**Exported:** 2024-11-28 15:30:45  
**Messages:** 150

---

## 2024-11-28

**[10:00:00] Alice:**
> Hello everyone!

**[10:01:23] Bob:**
> Hi Alice!

**[10:05:15] Carol:**
> Good morning!
```

### CSV
**Best for:** Spreadsheets, data analysis

```csv
timestamp,sender_id,sender_name,channel,content
2024-11-28T10:00:00Z,peer_abc123,Alice,#general,"Hello everyone!"
2024-11-28T10:01:23Z,peer_def456,Bob,#general,"Hi Alice!"
2024-11-28T10:05:15Z,peer_ghi789,Carol,#general,"Good morning!"
```

## Export Options

### Date Range Export

```
> /export #general --from 2024-11-01 --to 2024-11-28
[SYSTEM] Exported 450 messages (filtered by date) to exports/...
```

### Sender Filter

```
> /export #general --sender Alice
[SYSTEM] Exported 45 messages from Alice to exports/...
```

### Search and Export

```
> /export #general --search "roadmap"
[SYSTEM] Exported 12 messages matching "roadmap" to exports/...
```

### Include Metadata

```
> /export #general --full
[SYSTEM] Exported with full metadata (peer info, signatures, etc.)
```

## Importing Data

### Basic Import

```
> /import exports/general_20241128.json
[SYSTEM] Importing messages...
[SYSTEM] Imported 150 messages to #general
[SYSTEM] No duplicates detected
```

### Import to Specific Channel

```
> /import exports/dev_old.json --to #dev-archive
[SYSTEM] Imported 89 messages to #dev-archive
```

### Import with Deduplication

```
> /import exports/general.json --dedupe
[SYSTEM] Found 150 messages
[SYSTEM] Skipped 50 duplicates
[SYSTEM] Imported 100 new messages
```

### Merge Import

```
> /import exports/backup.json --merge
[SYSTEM] Merging with existing data...
[SYSTEM] Preserved newer messages
[SYSTEM] Imported 75 older messages
```

## Export Location

Default export directory:
```
tad/
  exports/
    general_20241128_153045.json
    dev_20241128_160000.txt
    secret_20241128_170000_encrypted.json
```

### Custom Export Path

```
> /export #general --output /backup/tad/
[SYSTEM] Exported to /backup/tad/general_20241128.json
```

## Private Channel Export

### Encrypted Export (Default)

```
> /export #secret
[SYSTEM] Exported 42 encrypted messages to exports/secret_20241128.json
```

Messages remain encrypted in the export file.

### Decrypted Export

```
> /export #secret --decrypt
⚠️  Warning: This will export messages in plain text!
Continue? (y/n): y
[SYSTEM] Exported 42 decrypted messages to exports/secret_20241128_decrypted.json
```

⚠️ **Security Warning:** Decrypted exports are not encrypted at rest!

## Automated Backups

### Daily Backup Script

Create `backup_tad.sh`:

```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup/tad/$DATE"

mkdir -p "$BACKUP_DIR"

# Export all channels
for channel in general dev team; do
    echo "/export #$channel json" | tad_cli >> "$BACKUP_DIR/export.log"
done

# Compress
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
rm -rf "$BACKUP_DIR"

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

Make executable and schedule with cron:
```bash
chmod +x backup_tad.sh
crontab -e
# Add: 0 2 * * * /path/to/backup_tad.sh
```

### Systemd Timer (Linux)

`/etc/systemd/system/tad-backup.service`:
```ini
[Unit]
Description=TAD Backup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup_tad.sh
User=tad
```

`/etc/systemd/system/tad-backup.timer`:
```ini
[Unit]
Description=Daily TAD Backup

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl enable tad-backup.timer
sudo systemctl start tad-backup.timer
```

## Migration Between Devices

### Full Migration

**On old device:**
```
> /export-all
[SYSTEM] Exporting all channels...
[SYSTEM] Exported 5 channels, 2,345 messages
[SYSTEM] Created: exports/full_backup_20241128.tar.gz
```

**On new device:**
```
> /import-all exports/full_backup_20241128.tar.gz
[SYSTEM] Importing full backup...
[SYSTEM] Restored 5 channels
[SYSTEM] Imported 2,345 messages
[SYSTEM] Migration complete!
```

### Selective Migration

Export specific channels on old device:
```
> /export #general
> /export #dev
> /export #team
```

Transfer files, then import on new device:
```
> /import exports/general_20241128.json
> /import exports/dev_20241128.json
> /import exports/team_20241128.json
```

## Data Analysis

### Convert to CSV for Analysis

```
> /export #general csv
```

Then in Python:
```python
import pandas as pd

df = pd.read_csv('exports/general_20241128.csv')

# Message frequency by sender
print(df['sender_name'].value_counts())

# Messages over time
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp').resample('D').size().plot()

# Word frequency
from collections import Counter
words = ' '.join(df['content']).lower().split()
Counter(words).most_common(20)
```

### Export Statistics

```
> /export #general --stats
[SYSTEM] Channel Statistics for #general:
  Total Messages: 1,234
  Unique Senders: 12
  Date Range: 2024-11-01 to 2024-11-28
  Most Active Hour: 15:00-16:00 (145 messages)
  Most Active Sender: Alice (234 messages)
  Average Message Length: 42 characters
```

## Troubleshooting

### Import Fails

**Problem:** Import returns errors.

**Solutions:**
1. Verify file format is valid JSON
2. Check file wasn't corrupted
3. Ensure channel exists or use `--create-channel`
4. Try `--force` flag to skip validation

```
> /import exports/backup.json --force --create-channel
```

### Large Export Slow

**Problem:** Exporting thousands of messages takes long.

**Solutions:**
1. Export in smaller date ranges
2. Use `--compress` for large exports
3. Export to SSD instead of network drive
4. Use `--batch` mode for parallel export

```
> /export #general --batch --compress
```

### Duplicate Messages After Import

**Problem:** Messages appear twice after import.

**Solution:**
```
> /dedupe #general
[SYSTEM] Scanning for duplicates...
[SYSTEM] Found 50 duplicate messages
[SYSTEM] Removed duplicates
```

## Best Practices

### Regular Backups

1. **Daily exports** for active channels
2. **Weekly full backups** of entire database
3. **Monthly archival** to external storage
4. **Test restores** quarterly

### Storage Management

```
# Keep last 7 days of exports
find exports/ -mtime +7 -delete

# Compress old exports
find exports/ -name "*.json" -mtime +1 -exec gzip {} \;
```

### Security

1. **Encrypt backups** of private channels
2. **Secure transfer** of export files
3. **Access control** on export directory
4. **Shred deleted** exports

```bash
# Secure delete
shred -u exports/secret_*.json

# Encrypt backup
gpg --encrypt exports/backup.tar.gz
```

## Advanced Features

### Custom Export Format

Create custom exporter:

```python
# custom_exporter.py
from tad.persistence.database import Database

db = Database()
messages = db.get_messages('#general')

# Custom format
with open('custom_export.xml', 'w') as f:
    f.write('<messages>\n')
    for msg in messages:
        f.write(f'  <message sender="{msg.sender}" '
                f'time="{msg.timestamp}">{msg.content}</message>\n')
    f.write('</messages>')
```

### Export API

Programmatic export:

```python
from tad.persistence.database import Database

db = Database()
data = db.export_channel('#general', format='json')

# Process or transfer
upload_to_cloud(data)
```

## See Also

- [Basic Usage](/guide/basic-usage) - General usage
- [Private Channels](/guide/private-channels) - Encrypted data
- [Commands](/guide/commands) - All commands
- [Database Reference](/reference/database) - Data structure
