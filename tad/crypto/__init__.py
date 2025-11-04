"""
TAD Cryptography Module (Milestone 6)

Provides End-to-End Encryption (E2EE) capabilities for secure channels:
- AES-256-GCM symmetric encryption for message content
- Key derivation and management
- Secure key exchange using sealed boxes
- Encryption/decryption utilities

Components:
- E2EEManager: Main encryption/decryption orchestration
"""

from .e2ee import E2EEManager

__all__ = ["E2EEManager"]
