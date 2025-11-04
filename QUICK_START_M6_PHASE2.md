# Milestone 6 Phase 2 - Quick Start Guide

## 🚀 Ready to Continue?

This guide helps you pick up where we left off and complete Milestone 6.

---

## Current State (Phase 1 ✅)

**What's already done:**
- ✅ E2EE cryptography module (`tad/crypto/e2ee.py`)
- ✅ Database schema with permissions (`tad/persistence/database.py`)
- ✅ New member management methods
- ✅ Detailed roadmap (see `MILESTONE_6_PROGRESS.md`)

**What's ready to implement:**
- 📋 Node.py integration
- 📋 TUI commands
- 📋 UI updates
- 📋 Test suite

---

## Phase 2 Implementation Checklist

### Step 1: Node.py Integration (~150-200 lines)

**File:** `tad/node.py`

**Add these imports:**
```python
from .crypto.e2ee import E2EEManager
```

**In `__init__`:**
```python
self.e2ee = E2EEManager()  # Initialize crypto manager
```

**Add these methods:**

#### A. Create Channel
```python
def create_channel(self, channel_id: str, channel_type: str = "public") -> bool:
    """
    Create a new channel.

    For private channels:
    - Generate symmetric key
    - Store in e2ee manager
    - Add owner as member
    - Save to database
    """
    # Implementation here
```

#### B. Invite Member
```python
def invite_to_channel(
    self,
    channel_id: str,
    recipient_node_id: str,
    recipient_public_key_hex: str
) -> bool:
    """
    Invite member to private channel.

    Process:
    1. Get channel key
    2. Encrypt with recipient's public key
    3. Send INVITE message
    """
    # Implementation here
```

#### C. Process Private Channel Messages
```python
def _process_message_for_channel(self, message: dict):
    """
    Updated message processing with E2EE support.

    For private channels:
    - Check membership
    - Get channel key
    - Decrypt content
    - Process normally
    """
    # Implementation here
```

---

### Step 2: TUI Commands (~100-150 lines)

**File:** `tad/main.py` - In `TADTUIApp` class

**Add command handlers:**

#### A. Create Command
```python
def _cmd_create(self, args: list) -> None:
    """
    Handle /create command.

    Usage: /create #channel-name [public|private]
    Example: /create #secret private
    """
    if len(args) < 1:
        self.message_view.add_command_output("Usage: /create <#channel> [public|private]")
        return

    channel_name = args[0]
    channel_type = args[1] if len(args) > 1 else "public"

    # Call self.node.create_channel(channel_name, channel_type)
```

#### B. Invite Command
```python
def _cmd_invite(self, args: list) -> None:
    """
    Handle /invite command.

    Usage: /invite <node_id> <#channel>
    Example: /invite alice123 #secret
    """
    if len(args) < 2:
        self.message_view.add_command_output("Usage: /invite <node_id> <#channel>")
        return

    node_id = args[0]
    channel_id = args[1]

    # Call self.node.invite_to_channel(channel_id, node_id, ...)
```

#### C. Register Commands
In `_handle_command()` method, add:
```python
elif command == "create":
    self._cmd_create(args)
elif command == "invite":
    self._cmd_invite(args)
elif command == "accept":
    self._cmd_accept(args)
```

---

### Step 3: UI Updates (~50-80 lines)

**File:** `tad/ui/widgets.py`

**Update ChannelItem class:**
```python
class ChannelItem(ListItem):
    def __init__(
        self,
        channel_id: str,
        unread_count: int = 0,
        is_active: bool = False,
        channel_type: str = "public",  # NEW
        **kwargs,
    ):
        # Add icon for channel type
        icon = "🔒" if channel_type == "private" else "🔓"
        label_text = f"{icon} {channel_id}"
        if unread_count > 0:
            label_text = f"{icon} {channel_id} ({unread_count})"

        super().__init__(Label(label_text), **kwargs)
```

**Update ChannelList class:**
```python
def add_channel(
    self,
    channel_id: str,
    channel_type: str = "public"  # NEW
) -> None:
    """Add a channel to the list."""
    if channel_id not in self.channel_items:
        item = ChannelItem(
            channel_id,
            is_active=(channel_id == self.active_channel),
            channel_type=channel_type  # NEW
        )
        self.channel_items[channel_id] = item
        list_view = self.query_one("#channel_list", ListView)
        list_view.append(item)
```

---

### Step 4: Test Suite (~400-500 lines)

**File:** `tests/test_milestone6_security.py`

**Create test file with these test classes:**

```python
import pytest
from tad.crypto.e2ee import E2EEManager
from tad.node import TADNode
from tad.persistence import DatabaseManager

class TestE2EECrypto:
    """Test encryption/decryption."""

    def test_encrypt_decrypt_message(self):
        """Test basic encryption/decryption."""
        key = E2EEManager.generate_channel_key()
        plaintext = "Secret message"

        ciphertext_hex, nonce_hex = E2EEManager.encrypt_message(key, plaintext)
        decrypted = E2EEManager.decrypt_message(key, ciphertext_hex, nonce_hex)

        assert decrypted == plaintext

    def test_wrong_key_fails(self):
        """Test decryption fails with wrong key."""
        key1 = E2EEManager.generate_channel_key()
        key2 = E2EEManager.generate_channel_key()

        ciphertext_hex, nonce_hex = E2EEManager.encrypt_message(key1, "Secret")
        decrypted = E2EEManager.decrypt_message(key2, ciphertext_hex, nonce_hex)

        assert decrypted is None

class TestChannelPermissions:
    """Test access control."""

    def test_create_public_channel(self):
        """Test creating public channel."""
        # Implementation
        pass

    def test_create_private_channel(self):
        """Test creating private channel."""
        # Implementation
        pass

    def test_membership_check(self):
        """Test membership validation."""
        # Implementation
        pass

class TestInviteFlow:
    """Test complete invite system."""

    def test_owner_invites_member(self):
        """Test invitation flow."""
        # Implementation
        pass

    def test_member_can_decrypt(self):
        """Test member receives and uses key."""
        # Implementation
        pass

    def test_non_member_cannot_decrypt(self):
        """Test access control enforcement."""
        # Implementation
        pass
```

**Run tests:**
```bash
pytest tests/test_milestone6_security.py -v
```

Expected: 20+ tests all passing ✅

---

## Quick Commands Reference

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run only Milestone 6 tests
```bash
python -m pytest tests/test_milestone6_security.py -v
```

### Run Milestone 5 tests (sanity check)
```bash
python -m pytest tests/test_milestone5_tui.py -v
```

### Check database schema
```bash
sqlite3 tad_node.db ".schema"
```

### View git status
```bash
git status
git log --oneline -10
```

---

## Architecture Reminder

```
TUI Commands (/create, /invite)
         ↓
    TADNode Methods
    ├─ create_channel()      → E2EEManager (generate key)
    ├─ invite_to_channel()   → E2EEManager (encrypt key)
    └─ message processing    → E2EEManager (decrypt/verify)
         ↓
    DatabaseManager
    ├─ Store channel info (type, owner)
    ├─ Manage members
    └─ Persist encrypted messages
         ↓
    Network Layer
    └─ Broadcast encrypted messages
```

---

## File Dependencies

When editing these files, remember:

1. **tad/node.py**
   - Depends on: `tad/crypto/e2ee.py`
   - Imports: `from .crypto.e2ee import E2EEManager`

2. **tad/main.py**
   - Depends on: `tad/node.py` (for create/invite methods)
   - Already imports: `from .node import TADNode`

3. **tad/ui/widgets.py**
   - Depends on: Existing Textual widgets (no changes to imports needed)

4. **tests/test_milestone6_security.py**
   - Depends on: All above modules
   - Imports: E2EEManager, TADNode, DatabaseManager

---

## Testing Strategy

### 1. Unit Tests (Individual components)
- E2EE encryption/decryption
- Key generation
- Channel creation
- Member management

### 2. Integration Tests (Full flows)
- Create private channel → Invite member → Send message → Decrypt
- Access control enforcement
- Non-member message rejection

### 3. Sanity Checks
- Verify all existing tests still pass
- Check database schema migrations
- Verify backward compatibility

---

## Documentation Checklist

After implementing Phase 2, update:
- [ ] FASE_1_MILESTONE_6_COMPLETE.md (similar to M5)
- [ ] README.md with new features
- [ ] Code comments in key methods
- [ ] Test suite docstrings

---

## Estimated Timeline

| Task | Time | Status |
|------|------|--------|
| Node.py integration | 1-2 hrs | 📋 Ready |
| TUI commands | 1 hr | 📋 Ready |
| UI updates | 30 min | 📋 Ready |
| Test suite | 2 hrs | 📋 Ready |
| Documentation | 1 hr | 📋 Ready |
| **TOTAL** | **5.5-6.5 hrs** | **Ready** |

---

## Key Reminders

✅ **DO:**
- Use type hints throughout
- Add comprehensive docstrings
- Test as you implement
- Commit frequently
- Check existing tests don't break

❌ **DON'T:**
- Store plaintext keys on disk
- Bypass encryption for private channels
- Remove backward compatibility
- Skip database migration testing

---

## Success Criteria

Phase 2 is complete when:
- ✅ All node.py methods implemented and tested
- ✅ All TUI commands working and tested
- ✅ UI shows channel type (public/private)
- ✅ 20+ security tests all passing
- ✅ Documentation complete
- ✅ All code committed to git

---

## Ready to Go!

Everything is set up and documented. Start with Step 1 (node.py integration) and work through each step. Reference `MILESTONE_6_PROGRESS.md` for detailed specifications.

Good luck! 🚀

