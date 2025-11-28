# Security Policy

## Supported Versions

The following versions of TAD are currently supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of TAD seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

**Please DO NOT open a public GitHub issue for security vulnerabilities.**

Instead, report security issues via email:

- **Email:** [fabriziosalmi@gmail.com](mailto:fabriziosalmi@gmail.com)
- **Subject:** "TAD Security Vulnerability Report"

### What to Include

Please include the following information in your report:

1. **Description:** A clear description of the vulnerability
2. **Impact:** Potential impact and severity assessment
3. **Steps to Reproduce:** Detailed steps to reproduce the issue
4. **Proof of Concept:** Code or commands demonstrating the vulnerability (if applicable)
5. **Suggested Fix:** If you have a proposed solution (optional)
6. **Environment:**
   - TAD version
   - Operating system and version
   - Python version
   - Any relevant configuration

### Example Report

```
Subject: TAD Security Vulnerability Report

Description:
Discovered a potential privilege escalation in the private channel invitation system.

Impact:
An attacker could gain unauthorized access to encrypted channels by forging
invitation messages. Severity: HIGH

Steps to Reproduce:
1. Create a private channel: /create #test private
2. Craft a malicious invitation message with modified node_id
3. Send via direct TCP connection
4. Observe unauthorized access granted

Environment:
- TAD v1.0.0
- Ubuntu 22.04
- Python 3.10.5

Suggested Fix:
Add signature verification to invitation messages using the channel owner's
Ed25519 key.
```

### Response Timeline

- **Initial Response:** Within 48 hours of receiving your report
- **Status Update:** Weekly updates on investigation progress
- **Resolution:** Target 30 days for critical vulnerabilities, 90 days for non-critical

### Process

1. **Acknowledgment:** We will acknowledge receipt of your report within 48 hours
2. **Investigation:** We will investigate and validate the vulnerability
3. **Communication:** We will keep you informed of our progress
4. **Fix Development:** We will develop and test a fix
5. **Disclosure:** We will coordinate disclosure timeline with you
6. **Release:** We will release a security update
7. **Credit:** We will credit you in the release notes (if desired)

## Security Best Practices

### For Users

1. **Keep TAD Updated:**
   ```bash
   cd tad
   git pull
   pip install -r requirements.txt --upgrade
   ```

2. **Protect Your Keys:**
   - Backup `profile.json` securely
   - Set file permissions: `chmod 600 profile.json`
   - Never share your private keys
   - Never commit `profile.json` to version control

3. **Secure Your Database:**
   - Set file permissions: `chmod 600 tad_node.db`
   - Regular backups using `/export`
   - Encrypt backups of private channel data

4. **Network Security:**
   - Use TAD only on trusted local networks
   - Configure firewall rules appropriately
   - Be aware that public channels are not encrypted
   - Verify peer identities before sharing sensitive information

5. **Private Channel Security:**
   - Only invite trusted peers to private channels
   - Be aware of metadata visibility (timing, size, channel names)
   - Consider using obscure channel names for sensitive topics

### For Developers

1. **Code Review:**
   - Review all cryptographic code changes carefully
   - Follow secure coding practices
   - Use static analysis tools

2. **Dependencies:**
   - Keep dependencies updated
   - Monitor security advisories for dependencies
   - Use `pip-audit` to scan for vulnerabilities:
     ```bash
     pip install pip-audit
     pip-audit
     ```

3. **Testing:**
   - Write security-focused unit tests
   - Test encryption/decryption edge cases
   - Validate signature verification
   - Test permission enforcement

4. **Cryptography:**
   - Never implement custom cryptography
   - Use well-established libraries (NaCl, cryptography)
   - Follow current best practices
   - Ensure proper key generation and storage

## Known Security Considerations

### Architecture Limitations

1. **Metadata Visibility:**
   - Channel names are visible in plaintext
   - Message timing and size are observable
   - Sender identities are visible

2. **Network Security:**
   - TAD is designed for local trusted networks
   - No built-in protection against network-level attacks
   - mDNS broadcasts are not encrypted
   - TCP connections are not TLS-wrapped (E2EE handles message encryption)

3. **Forward Secrecy:**
   - Current implementation does not support key rotation
   - Compromised channel keys can decrypt historical messages
   - Future: Implement ratcheting for forward secrecy

4. **Authentication:**
   - Peer authentication relies on Ed25519 signatures
   - No PKI or web of trust for key verification
   - Users must verify peer identities out-of-band

### Threat Model

**What TAD Protects Against:**
- ✅ Message content eavesdropping (private channels)
- ✅ Message tampering (signature verification)
- ✅ Unauthorized channel access (encryption)
- ✅ Identity spoofing (Ed25519 signatures)

**What TAD Does NOT Protect Against:**
- ❌ Network-level traffic analysis
- ❌ Compromised endpoints
- ❌ Social engineering attacks
- ❌ Physical access to device
- ❌ Advanced persistent threats

### Recommended Use Cases

**Appropriate:**
- Local community coordination
- Offline event communication
- Privacy-conscious group chat
- Decentralized team communication

**Not Recommended:**
- High-security government communications
- Financial transactions
- Legal privilege communications
- Whistleblower protection (use Tor-based systems instead)

## Security Features

### Current Implementation

1. **End-to-End Encryption:**
   - AES-256-GCM for message content
   - Authenticated encryption prevents tampering
   - Per-channel symmetric keys

2. **Key Exchange:**
   - X25519 elliptic curve Diffie-Hellman
   - NaCl SealedBox for key distribution
   - Public key encryption for invitations

3. **Message Signing:**
   - Ed25519 digital signatures
   - Prevents message forgery
   - Verifies sender identity

4. **Database Security:**
   - SQLite with restricted file permissions
   - Encrypted messages stored as ciphertext
   - Keys stored separately in `profile.json`

## Vulnerability Disclosure Policy

### Coordinated Disclosure

We follow a coordinated disclosure policy:

1. **Private Reporting:** Security researchers report privately
2. **Investigation:** We investigate and develop fixes
3. **Notification:** We notify affected users before public disclosure
4. **Disclosure:** We publish security advisories 30 days after fix release
5. **Credit:** We credit researchers in advisories (if desired)

### Security Advisories

Published advisories are available at:
- GitHub Security Advisories: https://github.com/fabriziosalmi/tad/security/advisories

### CVE Assignment

For significant vulnerabilities, we will request CVE assignment through GitHub.

## Security Audit

TAD has not undergone a formal security audit. We welcome independent security reviews and will coordinate with researchers.

## Questions?

For security-related questions that are not vulnerabilities:
- Open a [GitHub Discussion](https://github.com/fabriziosalmi/tad/discussions)
- Tag with "security" label

For vulnerabilities, always use private email reporting.

## Updates

This security policy was last updated: 2025-11-28

We will update this policy as the project evolves and new security considerations arise.
