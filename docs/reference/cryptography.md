# Cryptography

Technical details of TAD's cryptographic implementation.

## Overview

TAD uses modern cryptography to provide:
- **Identity verification** via public key cryptography
- **End-to-end encryption** for private channels
- **Message integrity** through digital signatures
- **Perfect forward secrecy** (roadmap)

## Identity System

### Key Generation

Each TAD node generates an Ed25519 key pair on first run:

```python
# Using cryptography library
from cryptography.hazmat.primitives.asymmetric import ed25519

# Generate private key
private_key = ed25519.Ed25519PrivateKey.generate()

# Derive public key
public_key = private_key.public_key()
```

**Key Properties:**
- **Algorithm:** Ed25519 (EdDSA)
- **Key Size:** 256 bits (32 bytes)
- **Security Level:** ~128-bit (equivalent to RSA-3072)
- **Performance:** Very fast signing and verification

### Key Storage

Keys are stored in the data directory:

```
tad_data/
  identity.key        # Private key (PEM format)
  identity.pub        # Public key (PEM format)
```

**File Permissions:** 
- `identity.key`: 600 (owner read/write only)
- `identity.pub`: 644 (world readable)

### Node Identifier

Node ID is derived from public key:

```python
import hashlib
import base64

node_id = base64.b32encode(
    hashlib.sha256(public_key_bytes).digest()[:20]
).decode('utf-8').lower()
```

**Format:** 32-character base32 string  
**Example:** `abcd1234efgh5678ijkl90mnopqrstuv`

## Message Signing

All messages are digitally signed for authenticity.

### Signature Creation

```python
from cryptography.hazmat.primitives import serialization

# Message to sign
message = b"Hello, TAD!"

# Sign with private key
signature = private_key.sign(message)
```

**Signature Properties:**
- **Algorithm:** Ed25519
- **Size:** 64 bytes (512 bits)
- **Deterministic:** Same message = same signature (with same key)

### Signature Verification

```python
from cryptography.exceptions import InvalidSignature

try:
    public_key.verify(signature, message)
    print("Valid signature")
except InvalidSignature:
    print("Invalid signature - reject message")
```

### Message Format

```json
{
  "sender": "abcd1234...",
  "timestamp": "2024-11-28T15:30:00Z",
  "channel": "#general",
  "content": "Hello, TAD!",
  "signature": "base64_encoded_signature",
  "public_key": "base64_encoded_public_key"
}
```

## Channel Encryption

Private channels use symmetric encryption with password-derived keys.

### Key Derivation

**Algorithm:** PBKDF2-HMAC-SHA256

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Derive key from password
kdf = PBKDF2HMAC(
    algorithm=hashes.SHA256(),
    length=32,              # 256-bit key
    salt=channel_salt,      # Random per-channel salt
    iterations=100000,      # Iteration count
)
key = kdf.derive(password.encode('utf-8'))
```

**Parameters:**
- **Salt:** 16 bytes random (per channel)
- **Iterations:** 100,000 (configurable)
- **Output:** 32 bytes (256-bit key)

### Encryption

**Algorithm:** AES-256-GCM

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Create cipher
aesgcm = AESGCM(key)

# Encrypt message
nonce = os.urandom(12)  # 96-bit nonce
ciphertext = aesgcm.encrypt(
    nonce,
    plaintext,
    associated_data=None
)
```

**Properties:**
- **Mode:** Galois/Counter Mode (GCM)
- **Key Size:** 256 bits
- **Nonce Size:** 96 bits (random per message)
- **Tag Size:** 128 bits (authentication tag)
- **Authenticated Encryption:** Provides confidentiality + integrity

### Encrypted Message Format

```json
{
  "channel": "#secret",
  "encrypted": true,
  "nonce": "base64_encoded_nonce",
  "ciphertext": "base64_encoded_encrypted_data",
  "tag": "base64_encoded_auth_tag"
}
```

### Decryption

```python
try:
    plaintext = aesgcm.decrypt(nonce, ciphertext, associated_data=None)
except InvalidTag:
    # Authentication failed - message tampered or wrong key
    raise DecryptionError("Invalid ciphertext or key")
```

## Security Analysis

### Threat Model

| Threat | Protection | Mechanism |
|--------|-----------|-----------|
| Eavesdropping | ✅ Protected | AES-256-GCM encryption |
| Message tampering | ✅ Protected | GCM authentication tag |
| Impersonation | ✅ Protected | Ed25519 signatures |
| Replay attacks | ⚠️ Partial | Timestamp checking |
| Man-in-the-middle | ❌ Limited | No key exchange protocol |
| Forward secrecy | ❌ None | Same key for all messages |

### Known Limitations

1. **No Perfect Forward Secrecy**
   - Same symmetric key encrypts all messages
   - Key compromise = all past messages decryptable
   - **Mitigation:** Regular password rotation

2. **Password-Based Encryption**
   - Security depends on password strength
   - Vulnerable to offline brute-force
   - **Mitigation:** Strong passwords, high iteration count

3. **No Peer Authentication in Encrypted Channels**
   - Can't verify sender within encrypted channel
   - Anyone with password can impersonate
   - **Mitigation:** Out-of-band verification

4. **Metadata Leakage**
   - Channel names visible
   - Message timing visible
   - Participant list visible
   - **Mitigation:** Use generic channel names

## Cryptographic Parameters

### Current Settings

```python
# Identity
IDENTITY_ALGORITHM = "Ed25519"
SIGNATURE_SIZE = 64  # bytes

# Key Derivation
KDF_ALGORITHM = "PBKDF2-HMAC-SHA256"
KDF_ITERATIONS = 100000
KDF_SALT_SIZE = 16  # bytes
KDF_OUTPUT_SIZE = 32  # bytes (256 bits)

# Encryption
ENCRYPTION_ALGORITHM = "AES-256-GCM"
ENCRYPTION_KEY_SIZE = 32  # bytes (256 bits)
ENCRYPTION_NONCE_SIZE = 12  # bytes (96 bits)
ENCRYPTION_TAG_SIZE = 16  # bytes (128 bits)
```

### Recommended Adjustments

For high-security deployments:

```python
# Increase PBKDF2 iterations
KDF_ITERATIONS = 500000  # or higher

# Use longer passwords
MIN_PASSWORD_LENGTH = 20

# Implement key rotation
KEY_ROTATION_INTERVAL = 30 * 24 * 3600  # 30 days
```

## Implementation Details

### Message Encryption Flow

```
Plaintext Message
       ↓
1. Generate random nonce (12 bytes)
       ↓
2. Derive key from password (if not cached)
       ↓
3. Encrypt with AES-256-GCM
       ↓
4. Encode nonce + ciphertext + tag as base64
       ↓
5. Create encrypted message JSON
       ↓
6. Sign entire message (outer signature)
       ↓
Encrypted + Signed Message
```

### Message Decryption Flow

```
Encrypted Message
       ↓
1. Verify outer signature
       ↓
2. Extract nonce, ciphertext, tag
       ↓
3. Derive key from password (if not cached)
       ↓
4. Decrypt with AES-256-GCM
       ↓
5. Verify authentication tag
       ↓
6. Parse plaintext
       ↓
Plaintext Message
```

## Key Management

### Key Derivation Caching

```python
# Cache derived keys to avoid repeated PBKDF2
key_cache = {
    "#channel_name": {
        "key": derived_key,
        "timestamp": time.time(),
        "ttl": 3600  # 1 hour
    }
}
```

### Key Rotation

```python
# Rotate channel key
def rotate_channel_key(channel, old_password, new_password):
    # 1. Derive new key
    new_key = derive_key(new_password, channel.salt)
    
    # 2. Re-encrypt all messages (optional)
    for msg in channel.messages:
        plaintext = decrypt(msg, old_key)
        encrypted = encrypt(plaintext, new_key)
        update_message(msg.id, encrypted)
    
    # 3. Update channel password hash
    channel.password_hash = hash_password(new_password)
```

## Security Best Practices

### For Users

1. **Strong Passwords**
   ```python
   # Generate strong password
   import secrets
   password = secrets.token_urlsafe(32)
   ```

2. **Regular Rotation**
   - Rotate passwords every 30-90 days
   - Use `/rekey` command

3. **Secure Sharing**
   - Share passwords out-of-band
   - Never in plain text channels

### For Developers

1. **Constant-Time Operations**
   ```python
   # Use constant-time comparison
   import hmac
   
   def compare_signatures(sig1, sig2):
       return hmac.compare_digest(sig1, sig2)
   ```

2. **Secure Random Generation**
   ```python
   # Use cryptographically secure random
   import secrets
   
   nonce = secrets.token_bytes(12)
   salt = secrets.token_bytes(16)
   ```

3. **Memory Safety**
   ```python
   # Clear sensitive data from memory
   import ctypes
   
   def clear_memory(data):
       ctypes.memset(id(data), 0, len(data))
   ```

## Cryptographic Libraries

TAD uses these well-audited libraries:

### cryptography (primary)

```python
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

**Version:** 41.0.0+  
**License:** Apache 2.0 / BSD  
**Audit Status:** Well-audited, industry standard

## Future Enhancements

### Signal Protocol Integration

Planned implementation of the Signal Protocol for:
- Perfect forward secrecy
- Break-in recovery
- Deniable authentication

### Post-Quantum Cryptography

Evaluation of post-quantum algorithms:
- **CRYSTALS-Kyber** for key exchange
- **CRYSTALS-Dilithium** for signatures
- **SPHINCS+** as fallback

### Hardware Security Module Support

Support for hardware keys:
- YubiKey integration
- TPM support
- Hardware-backed key storage

## Testing

### Cryptographic Tests

```bash
# Run crypto test suite
python -m pytest tests/test_crypto.py -v

# Benchmark performance
python -m tad.crypto.benchmark
```

### Known Answer Tests (KAT)

Verify against test vectors:

```python
# Test AES-256-GCM
def test_aes_gcm_kat():
    key = bytes.fromhex("...")
    nonce = bytes.fromhex("...")
    plaintext = bytes.fromhex("...")
    expected_ciphertext = bytes.fromhex("...")
    
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    assert ciphertext == expected_ciphertext
```

## References

- [RFC 8032](https://tools.ietf.org/html/rfc8032) - Edwards-Curve Digital Signature Algorithm (EdDSA)
- [RFC 5869](https://tools.ietf.org/html/rfc5869) - HMAC-based Extract-and-Expand Key Derivation Function (HKDF)
- [NIST SP 800-38D](https://csrc.nist.gov/publications/detail/sp/800-38d/final) - Galois/Counter Mode (GCM)
- [NIST SP 800-132](https://csrc.nist.gov/publications/detail/sp/800-132/final) - Password-Based Key Derivation

## See Also

- [Private Channels](/guide/private-channels) - Using encryption
- [Security](/guide/security) - Security hardening
- [Architecture](/reference/architecture) - System design
