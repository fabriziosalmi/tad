"""
TAD End-to-End Encryption (E2EE) Module (Milestone 6)

Provides secure encryption and key exchange for private channels:

- Channel Keys: Each private channel has a unique AES-256-GCM symmetric key
- Key Exchange: Symmetric keys transmitted via asymmetric encryption (SealedBox)
- Message Encryption: Content encrypted with channel key, authenticated with GCM tag
- Key Derivation: Deterministic key generation from channel information

Security Model:
1. Channel owner generates a symmetric key for the channel
2. Owner encrypts the key with each member's public key (SealedBox)
3. Only members who decrypt the key can read channel messages
4. Each message authenticated with AEAD (GCM tag)
5. Replay attack prevention through message signatures (from M2)
"""

import json
import logging
import os
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from nacl.public import SealedBox, PublicKey, PrivateKey
from nacl.utils import random

logger = logging.getLogger(__name__)


class E2EEManager:
    """
    Manages End-to-End Encryption for TAD channels.

    Responsibilities:
    - Generate symmetric keys for channels
    - Encrypt/decrypt message content using AES-256-GCM
    - Safely transmit channel keys to new members (SealedBox)
    - Manage channel key storage and retrieval
    """

    # Channel keys storage: {channel_id: bytes}
    def __init__(self):
        """Initialize the E2EE manager."""
        self.channel_keys: Dict[str, bytes] = {}
        logger.info("E2EEManager initialized")

    # ============================================================
    # Channel Key Generation and Management
    # ============================================================

    @staticmethod
    def generate_channel_key() -> bytes:
        """
        Generate a new symmetric key for a channel.

        Returns:
            32-byte key suitable for AES-256-GCM
        """
        return os.urandom(32)  # 256 bits for AES-256

    def store_channel_key(self, channel_id: str, key: bytes) -> None:
        """
        Store a channel key in memory.

        Args:
            channel_id: Channel identifier
            key: 32-byte symmetric key
        """
        if len(key) != 32:
            raise ValueError(f"Channel key must be 32 bytes, got {len(key)}")

        self.channel_keys[channel_id] = key
        logger.debug(f"Stored key for channel {channel_id}")

    def get_channel_key(self, channel_id: str) -> Optional[bytes]:
        """
        Retrieve a stored channel key.

        Args:
            channel_id: Channel identifier

        Returns:
            The channel key, or None if not stored
        """
        return self.channel_keys.get(channel_id)

    def has_channel_key(self, channel_id: str) -> bool:
        """
        Check if we have a key for this channel.

        Args:
            channel_id: Channel identifier

        Returns:
            True if we have the channel key
        """
        return channel_id in self.channel_keys

    # ============================================================
    # Message Encryption and Decryption (AES-256-GCM)
    # ============================================================

    @staticmethod
    def encrypt_message(channel_key: bytes, plaintext: str) -> Tuple[str, str]:
        """
        Encrypt a message using AES-256-GCM.

        Args:
            channel_key: 32-byte symmetric key for the channel
            plaintext: Message content to encrypt

        Returns:
            Tuple of (ciphertext_hex, nonce_hex) both as hex strings
        """
        if len(channel_key) != 32:
            raise ValueError(f"Channel key must be 32 bytes, got {len(channel_key)}")

        # Generate random nonce (96 bits for GCM)
        nonce = os.urandom(12)

        # Create cipher
        cipher = AESGCM(channel_key)

        # Encrypt with authentication
        plaintext_bytes = plaintext.encode("utf-8")
        ciphertext = cipher.encrypt(nonce, plaintext_bytes, None)

        # Return as hex strings for easy serialization
        return (
            ciphertext.hex(),
            nonce.hex(),
        )

    @staticmethod
    def decrypt_message(
        channel_key: bytes, ciphertext_hex: str, nonce_hex: str
    ) -> Optional[str]:
        """
        Decrypt a message using AES-256-GCM.

        Args:
            channel_key: 32-byte symmetric key for the channel
            ciphertext_hex: Encrypted message as hex string
            nonce_hex: Nonce as hex string

        Returns:
            Decrypted plaintext message, or None if decryption fails
        """
        try:
            if len(channel_key) != 32:
                raise ValueError(f"Channel key must be 32 bytes, got {len(channel_key)}")

            # Convert from hex
            ciphertext = bytes.fromhex(ciphertext_hex)
            nonce = bytes.fromhex(nonce_hex)

            # Create cipher and decrypt
            cipher = AESGCM(channel_key)
            plaintext_bytes = cipher.decrypt(nonce, ciphertext, None)

            return plaintext_bytes.decode("utf-8")

        except Exception as e:
            logger.warning(f"Failed to decrypt message: {e}")
            return None

    # ============================================================
    # Key Exchange (Asymmetric Encryption)
    # ============================================================

    @staticmethod
    def encrypt_key_for_recipient(
        recipient_public_key_hex: str, channel_key: bytes
    ) -> str:
        """
        Encrypt a channel key for a specific recipient using SealedBox.

        This allows the channel owner to securely transmit the symmetric
        channel key to new members. Only the recipient can decrypt it
        with their private key.

        Args:
            recipient_public_key_hex: Recipient's public key as hex string (32 bytes)
            channel_key: The symmetric channel key to encrypt (32 bytes)

        Returns:
            Encrypted key as hex string
        """
        try:
            # Reconstruct public key from hex
            public_key_bytes = bytes.fromhex(recipient_public_key_hex)
            recipient_public_key = PublicKey(public_key_bytes)

            # Create sealed box and encrypt
            sealed_box = SealedBox(recipient_public_key)
            encrypted_key = sealed_box.encrypt(channel_key)

            return encrypted_key.hex()

        except Exception as e:
            logger.error(f"Failed to encrypt key for recipient: {e}")
            raise

    @staticmethod
    def decrypt_key_from_sender(
        private_key_hex: str, encrypted_key_hex: str
    ) -> Optional[bytes]:
        """
        Decrypt a channel key received from the channel owner.

        Args:
            private_key_hex: This node's private key as hex string (32 bytes)
            encrypted_key_hex: Encrypted channel key as hex string

        Returns:
            The decrypted channel key (32 bytes), or None if decryption fails
        """
        try:
            # Reconstruct private key from hex
            private_key_bytes = bytes.fromhex(private_key_hex)
            private_key = PrivateKey(private_key_bytes)

            # Create sealed box and decrypt
            sealed_box = SealedBox(private_key)
            encrypted_key_bytes = bytes.fromhex(encrypted_key_hex)
            channel_key = sealed_box.decrypt(encrypted_key_bytes)

            if len(channel_key) != 32:
                raise ValueError(
                    f"Decrypted key must be 32 bytes, got {len(channel_key)}"
                )

            return channel_key

        except Exception as e:
            logger.warning(f"Failed to decrypt key from sender: {e}")
            return None

    # ============================================================
    # Key Derivation (For consistent key generation)
    # ============================================================

    @staticmethod
    def derive_key_from_password(
        password: str, salt: bytes = None, iterations: int = 100000
    ) -> Tuple[bytes, str]:
        """
        Derive a strong key from a password using PBKDF2.

        (Optional utility - can be used for key recovery or testing)

        Args:
            password: Password to derive key from
            salt: Random salt (generated if not provided)
            iterations: Number of PBKDF2 iterations

        Returns:
            Tuple of (key, salt_hex) where salt_hex can be stored
        """
        if salt is None:
            salt = os.urandom(16)

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations,
        )

        key = kdf.derive(password.encode("utf-8"))
        return key, salt.hex()

    # ============================================================
    # Utility Methods
    # ============================================================

    def clear_channel_key(self, channel_id: str) -> None:
        """
        Remove a channel key from memory.

        Args:
            channel_id: Channel identifier
        """
        if channel_id in self.channel_keys:
            del self.channel_keys[channel_id]
            logger.debug(f"Cleared key for channel {channel_id}")

    def clear_all_keys(self) -> None:
        """Clear all stored channel keys from memory."""
        self.channel_keys.clear()
        logger.info("Cleared all channel keys")

    def get_managed_channels(self) -> list:
        """
        Get list of channels we have keys for.

        Returns:
            List of channel IDs
        """
        return list(self.channel_keys.keys())
