# Channels

Learn how to create, manage, and use channels in TAD.

## What are Channels?

Channels in TAD are like chat rooms - isolated spaces where groups of peers can communicate. All peers on the network can see and join public channels.

## Types of Channels

### Public Channels
- Visible to all peers
- Anyone can join
- Messages broadcast to all channel members
- Default: `#general`

### Private Channels
- End-to-end encrypted
- Require password to join
- See [Private Channels](/guide/private-channels) for details

## Channel Names

Channel names must:
- Start with `#`
- Contain only alphanumeric characters, hyphens, and underscores
- Be 2-50 characters long

### Valid Examples
```
#general
#dev-team
#project_alpha
#room123
```

### Invalid Examples
```
general     # Missing #
#a          # Too short
#my channel # Contains space
#special!   # Invalid character
```

## Creating Channels

### Create Public Channel
```
> /create #myteam
[SYSTEM] Created channel #myteam
[SYSTEM] Switched to #myteam
```

You're automatically switched to new channels upon creation.

### Create and Share
After creating, other peers will discover the channel automatically through gossip protocol. They can join with:

```
> /join #myteam
```

## Joining Channels

### Join Existing Channel
```
> /channels
Available channels:
  #general
  #dev
* #myteam (current)

> /join #dev
[SYSTEM] Joined #dev
[SYSTEM] Switched to #dev
```

### Auto-Join on Discovery
TAD can auto-join channels when discovered (configurable).

## Switching Between Channels

```
> /switch #general
[SYSTEM] Switched to #general

> /switch #dev
[SYSTEM] Switched to #dev
```

**Shortcut:** The active channel is marked with `*` in the channel list.

## Listing Channels

### View All Channels
```
> /channels
Available channels:
* #general (current, 5 peers)
  #dev (3 peers)
  #random (2 peers)
  #private-room (encrypted, 1 peer)
```

### Channel Information
```
> /info #general
Channel: #general
Type: Public
Created: 2024-11-28 10:30:00
Messages: 1,234
Peers: 5
Last Activity: 2 minutes ago
```

## Leaving Channels

### Leave Current Channel
```
> /leave
[SYSTEM] Left #dev
[SYSTEM] Switched to #general
```

### Leave Specific Channel
```
> /leave #random
[SYSTEM] Left #random
```

⚠️ **Note:** You cannot leave `#general` - it's the default channel.

## Channel Persistence

- Channels are stored in your local database
- You automatically rejoin channels on restart
- Channel history is preserved locally
- Channels sync across peers through gossip

## Channel Discovery

TAD uses **gossip protocol** for channel discovery:

1. You create `#newchannel`
2. Your node announces it to connected peers
3. Those peers announce to their peers
4. Within seconds, the entire network knows

### Discovery Timeline
- **Local peers:** Instant
- **2 hops away:** 1-2 seconds
- **3+ hops:** 2-5 seconds

## Default Channel

`#general` is created automatically and cannot be deleted. It serves as:
- Landing channel for new users
- Fallback when leaving all other channels
- Network-wide announcement channel

## Channel Limits

- **Max channels per node:** 100
- **Max peers per channel:** Unlimited (network dependent)
- **Channel name length:** 2-50 characters
- **Max channels network-wide:** Unlimited

## Best Practices

### Naming Conventions
```
#general       - Main discussion
#dev           - Development talk
#announcements - Important updates only
#random        - Off-topic chat
#project-X     - Project-specific
```

### Organization Tips

1. **Use descriptive names**
   ```
   Good: #frontend-team
   Bad: #ft
   ```

2. **Create topic channels**
   ```
   #bug-reports
   #feature-requests
   #support
   ```

3. **Temporary channels**
   ```
   #event-2024-11-28
   #sprint-planning
   ```

4. **Privacy levels**
   ```
   #public-general    - Open discussion
   #team-private      - Password protected
   #admin-secure      - Highly restricted
   ```

## Channel Moderation

Currently TAD has limited moderation features:

### Block Peers
```
> /kick peer_abc123
[SYSTEM] Blocked peer_abc123
```

This prevents receiving messages from specific peers locally.

### Future Features
- Channel ownership
- Kick/ban capabilities
- Channel-level permissions
- Invite-only channels

## Troubleshooting

### Channel Not Appearing

**Problem:** Created channel but peers can't see it.

**Solutions:**
1. Wait 10-30 seconds for gossip propagation
2. Check network connectivity with `/peers`
3. Verify peer is running compatible TAD version
4. Try `/resync` to force sync

### Can't Join Channel

**Problem:** `/join #channel` fails.

**Solutions:**
1. Verify channel name spelling (case-sensitive)
2. Check if it's a private channel (use `/join-private`)
3. Ensure you're connected to peers with `/peers`

### Messages Not Syncing

**Problem:** Send message but it doesn't appear on other peers.

**Solutions:**
1. Check channel with `/info #channelname`
2. Verify peers in channel: `/peers`
3. Try switching away and back: `/switch #other` then `/switch #original`
4. Force resync: `/resync #channelname`

## Advanced Usage

### Channel Scripts

You can script channel operations:

```bash
# Create multiple channels
echo "/create #alpha" | python -m tad.main
echo "/create #beta" | python -m tad.main
```

### Monitoring Channels

Use `/status` to see channel activity:

```
> /status
Channels: 5 active
- #general: 234 messages (2 unread)
- #dev: 89 messages (0 unread)
- #random: 456 messages (12 unread)
```

## See Also

- [Private Channels](/guide/private-channels) - Encrypted channels
- [Commands](/guide/commands) - Full command reference
- [Gossip Protocol](/reference/api-gossip) - Technical details
- [Basic Usage](/guide/basic-usage) - General usage guide
