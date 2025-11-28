# Private Channels

End-to-end encrypted channels for secure communication.

## Overview

Private channels in TAD provide **end-to-end encryption** using symmetric AES-256-GCM encryption. Messages are encrypted before leaving your device and can only be decrypted by peers who know the password.

## Security Features

- 🔒 **AES-256-GCM encryption**
- 🔑 **Password-derived keys** (PBKDF2 with 100,000 iterations)
- 🛡️ **Authenticated encryption** (prevents tampering)
- 🔐 **Per-message nonces** (prevents replay attacks)
- 🚫 **No key exchange** (password must be shared out-of-band)

## Creating Private Channels

### Basic Creation
```
> /create-private #secret mypassword123
[SYSTEM] Created private channel #secret
[SYSTEM] Channel is E2E encrypted with AES-256-GCM
[SYSTEM] Switched to #secret
```

### Strong Password Recommendations

❌ **Weak passwords:**
```
#secret password
#secret 12345
#secret admin
```

✅ **Strong passwords:**
```
#secret Tr0ub4dor&3-Correct-Horse-Battery
#secret xK9$mP2#nQ8@vL5^wR7!
#secret randomly-generated-passphrase-with-words
```

### Password Requirements
- Minimum 8 characters recommended
- Use mix of letters, numbers, symbols
- Avoid common words or patterns
- Unique per channel

## Joining Private Channels

### Join Existing Private Channel
```
> /join-private #secret mypassword123
[SYSTEM] Joined private channel #secret
[SYSTEM] Decrypting message history...
[SYSTEM] Switched to #secret
```

### Wrong Password
```
> /join-private #secret wrongpassword
[ERROR] Failed to decrypt channel. Incorrect password?
```

## Using Private Channels

Once joined, private channels work like public channels:

```
> /switch #secret
> This message is encrypted!
[You] This message is encrypted!

> /info #secret
Channel: #secret
Type: Private (E2E encrypted)
Encryption: AES-256-GCM
Created: 2024-11-28 15:30:00
Messages: 42 (all encrypted)
Peers: 3
```

## Security Considerations

### Password Distribution

⚠️ **Critical:** Passwords must be shared securely:

**Good methods:**
- In-person exchange
- Separate secure channel (Signal, etc.)
- Password manager share
- Encrypted email

**Bad methods:**
- Public channels
- Unencrypted email
- SMS
- Written notes

### Who Can See What?

| Aspect | Network Observer | TAD Peer without Password | TAD Peer with Password |
|--------|------------------|---------------------------|------------------------|
| Channel exists | ✅ Yes | ✅ Yes | ✅ Yes |
| Channel name | ✅ Yes | ✅ Yes | ✅ Yes |
| Message count | ✅ Yes | ✅ Yes | ✅ Yes |
| Who's participating | ✅ Yes | ✅ Yes | ✅ Yes |
| Message content | ❌ No | ❌ No | ✅ Yes |
| Metadata (timestamps) | ✅ Yes | ✅ Yes | ✅ Yes |

### Metadata Leakage

Private channels **DO NOT hide:**
- Channel existence and name
- Number of messages
- Timing of messages  
- Participating peers
- Message sizes

Private channels **DO hide:**
- Message content
- Sender identity (within channel)
- Attachments (future feature)

## Advanced Features

### Change Channel Password

```
> /rekey #secret oldpassword newpassword
[SYSTEM] Re-encrypting channel #secret...
[SYSTEM] Re-encrypted 156 messages
[SYSTEM] Channel password updated
```

⚠️ All peers must update to new password.

### Export Encrypted Data

```
> /export #secret encrypted
[SYSTEM] Exported encrypted data to exports/secret_encrypted.json
```

Export formats:
- `encrypted` - Keep messages encrypted
- `decrypted` - Plain text export (use carefully!)

### Verify Encryption

```
> /verify #secret
[SYSTEM] Channel: #secret
[SYSTEM] Encryption: AES-256-GCM
[SYSTEM] Key derivation: PBKDF2-HMAC-SHA256 (100,000 iterations)
[SYSTEM] All messages encrypted: ✅
[SYSTEM] No decryption errors: ✅
```

## Comparing Public vs Private Channels

| Feature | Public Channel | Private Channel |
|---------|---------------|-----------------|
| Encryption | ❌ No | ✅ Yes (AES-256-GCM) |
| Password required | ❌ No | ✅ Yes |
| Visible to all | ✅ Yes | ⚠️ Name visible, content encrypted |
| Auto-join | ✅ Possible | ❌ Must know password |
| Performance | Faster | Slightly slower (encryption overhead) |
| Storage | Plain text | Encrypted |

## Threat Model

### Private Channels Protect Against:

✅ **Network eavesdropping** - Traffic is encrypted
✅ **Malicious peers** - Can't read without password
✅ **Database theft** - Messages stored encrypted
✅ **Local access** - Database encrypted at rest

### Private Channels DO NOT Protect Against:

❌ **Compromised password** - Anyone with password can decrypt
❌ **Metadata analysis** - Timing and patterns visible
❌ **Endpoint compromise** - If device hacked, messages visible
❌ **Key logger** - Password can be captured when typed
❌ **Traffic analysis** - Can see who talks when

## Best Practices

### For Maximum Security

1. **Use strong, unique passwords**
   ```
   Generate with: openssl rand -base64 32
   ```

2. **Share passwords securely**
   - Never in TAD public channels
   - Use established secure channels

3. **Regular password rotation**
   ```
   > /rekey #secret oldpass newpass
   ```
   Rotate every 30-90 days for high-security needs.

4. **Limit participants**
   - Fewer people = less risk
   - Verify all participants

5. **Monitor access**
   ```
   > /info #secret
   Peers: 3  # Should match expected number
   ```

### For Team Use

1. **Document password sharing process**
   - Who can share passwords
   - How passwords are distributed
   - When to rotate

2. **Use hierarchical channels**
   ```
   #team-public      - No password
   #team-private     - Team password
   #team-sensitive   - Leadership only
   ```

3. **Regular audits**
   ```
   > /info #sensitive
   ```
   Review who has access.

## Troubleshooting

### Can't Decrypt Messages

**Problem:** Joined private channel but see encrypted gibberish.

**Solutions:**
1. Verify password is correct
2. Check if password was recently changed
3. Try rejoining: `/leave` then `/join-private #channel password`

### Performance Issues

**Problem:** Private channels are slow.

**Explanation:** Encryption adds ~1-5ms per message. For large histories:
- Initial join: Decrypts all history
- Sending: Encrypts before transmission

**Solutions:**
1. Clear old messages: `/clear #channel`
2. Export and archive: `/export #channel`

### Password Forgotten

**Problem:** Lost password to private channel.

**Solution:** 
There is **no password recovery**. Encrypted data cannot be decrypted without the password. This is a security feature, not a bug.

Options:
- Ask channel members for password
- If no one remembers, channel is permanently inaccessible
- Create new channel with new password

## Technical Details

### Encryption Algorithm

```
Algorithm: AES-256-GCM
Mode: Galois/Counter Mode (GCM)
Key Size: 256 bits
Nonce Size: 96 bits (random, per-message)
Tag Size: 128 bits (authentication)
```

### Key Derivation

```
Algorithm: PBKDF2-HMAC-SHA256
Iterations: 100,000
Salt: Per-channel random salt (stored with channel metadata)
Output: 256-bit key
```

### Message Format

```python
encrypted_message = {
    "nonce": "base64_encoded_nonce",
    "ciphertext": "base64_encoded_encrypted_data",
    "tag": "base64_encoded_auth_tag"
}
```

## Limitations

### Current Limitations

- Password shared out-of-band (no key exchange protocol)
- No forward secrecy (same password encrypts all messages)
- No peer authentication within channel
- Metadata not hidden
- No plausible deniability

### Future Enhancements

- [ ] Signal Protocol integration (forward secrecy)
- [ ] Key rotation automation
- [ ] Metadata obfuscation
- [ ] Post-quantum cryptography
- [ ] Hardware key support

## See Also

- [Cryptography Reference](/reference/cryptography) - Technical details
- [Security Guide](/guide/security) - Hardening TAD
- [Channels](/guide/channels) - Public channels
- [Commands](/guide/commands) - All commands
