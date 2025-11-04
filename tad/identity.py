"""
TAD Identity Management

This module manages node identity:
- Ed25519 cryptographic key generation and persistence
- Profile management (username, keys)
- Secure identity loading/creation
- Message signing capabilities
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple

import nacl.encoding
import nacl.signing

logger = logging.getLogger(__name__)


class Identity:
    """
    Represents a node's cryptographic identity.

    Contains:
    - username: Human-readable username
    - signing_key: Private key for signing messages
    - verify_key: Public key for verifying signatures
    - verify_key_hex: Hex-encoded public key for network transmission
    """

    def __init__(
        self,
        username: str,
        signing_key: nacl.signing.SigningKey,
        verify_key: nacl.signing.VerifyKey,
    ):
        """
        Initialize an Identity.

        Args:
            username: Human-readable username
            signing_key: Private signing key
            verify_key: Public verification key
        """
        self.username = username
        self.signing_key = signing_key
        self.verify_key = verify_key
        # Hex-encoded public key for network transmission
        self.verify_key_hex = verify_key.encode(
            encoder=nacl.encoding.HexEncoder
        ).decode("utf-8")

    def __repr__(self) -> str:
        return f"Identity(username='{self.username}', verify_key_hex='{self.verify_key_hex[:16]}...')"


class IdentityManager:
    """
    Manages node identity: generation, persistence, and retrieval.

    Responsibilities:
    - Load existing identity from file
    - Generate new identity if not found
    - Persist identity to disk
    - Provide secure access to cryptographic keys
    """

    # File format version for compatibility
    FORMAT_VERSION = "1.0"

    def __init__(self, profile_path: str = "profile.json"):
        """
        Initialize the IdentityManager.

        Args:
            profile_path: Path to store the profile.json file
        """
        self.profile_path = Path(profile_path)
        self.identity: Optional[Identity] = None

    def load_or_create(self, username: str) -> Identity:
        """
        Load existing identity from disk, or create a new one.

        This is the main entry point for identity management.

        Args:
            username: Username to use if creating a new identity

        Returns:
            Identity object with keys loaded or created
        """
        if self.profile_path.exists():
            logger.info(f"Loading identity from {self.profile_path}")
            self.identity = self._load_from_file(username)
        else:
            logger.info(f"Creating new identity and saving to {self.profile_path}")
            self.identity = self._create_and_save_identity(username)

        return self.identity

    def _load_from_file(self, username: str) -> Identity:
        """
        Load identity from the profile.json file.

        Args:
            username: Username (for validation/display)

        Returns:
            Loaded Identity object

        Raises:
            ValueError: If profile file is corrupted or invalid
        """
        try:
            with open(self.profile_path, "r") as f:
                profile_data = json.load(f)

            # Validate format version
            version = profile_data.get("version")
            if version != self.FORMAT_VERSION:
                raise ValueError(
                    f"Unsupported profile version: {version} "
                    f"(expected {self.FORMAT_VERSION})"
                )

            # Extract profile data
            saved_username = profile_data.get("username")
            signing_key_hex = profile_data.get("signing_key_hex")

            if not saved_username or not signing_key_hex:
                raise ValueError("Profile missing required fields")

            # Reconstruct keys from hex encoding
            signing_key = nacl.signing.SigningKey(
                signing_key_hex, encoder=nacl.encoding.HexEncoder
            )
            verify_key = signing_key.verify_key

            logger.info(f"Identity loaded successfully (username: {saved_username})")

            return Identity(
                username=saved_username,
                signing_key=signing_key,
                verify_key=verify_key,
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Profile file is corrupted: {e}")
        except Exception as e:
            raise ValueError(f"Error loading profile: {e}")

    def _create_and_save_identity(self, username: str) -> Identity:
        """
        Create a new identity and save it to disk.

        Args:
            username: Username for the new identity

        Returns:
            Newly created Identity object
        """
        # Generate new signing key (Ed25519)
        signing_key = nacl.signing.SigningKey.generate()
        verify_key = signing_key.verify_key

        # Create identity object
        identity = Identity(
            username=username,
            signing_key=signing_key,
            verify_key=verify_key,
        )

        # Encode keys as hex strings for storage
        signing_key_hex = signing_key.encode(
            encoder=nacl.encoding.HexEncoder
        ).decode("utf-8")
        verify_key_hex = identity.verify_key_hex

        # Create profile dictionary
        profile_data = {
            "version": self.FORMAT_VERSION,
            "username": username,
            "signing_key_hex": signing_key_hex,
            "verify_key_hex": verify_key_hex,
        }

        # Save to file
        try:
            self.profile_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.profile_path, "w") as f:
                json.dump(profile_data, f, indent=2)

            # Restrict file permissions for security
            self.profile_path.chmod(0o600)

            logger.info(
                f"New identity created and saved to {self.profile_path} "
                f"(username: {username})"
            )

        except Exception as e:
            logger.error(f"Error saving profile: {e}")
            raise

        return identity

    def get_identity(self) -> Optional[Identity]:
        """
        Get the current loaded identity.

        Returns:
            Identity object or None if not loaded
        """
        return self.identity

    def sign_data(self, data: bytes) -> bytes:
        """
        Sign data with the private key.

        Args:
            data: Raw bytes to sign

        Returns:
            Digital signature (Signature object as bytes)

        Raises:
            RuntimeError: If no identity is loaded
        """
        if not self.identity:
            raise RuntimeError("No identity loaded. Call load_or_create() first.")

        return self.identity.signing_key.sign(data).signature

    def get_public_key_hex(self) -> str:
        """
        Get the hex-encoded public key.

        Returns:
            Public key as hex string

        Raises:
            RuntimeError: If no identity is loaded
        """
        if not self.identity:
            raise RuntimeError("No identity loaded. Call load_or_create() first.")

        return self.identity.verify_key_hex

    @staticmethod
    def verify_signature(
        message_bytes: bytes, signature_bytes: bytes, public_key_hex: str
    ) -> bool:
        """
        Verify a signature using a public key.

        This is a static method so it can be called without an instance.

        Args:
            message_bytes: The original message that was signed
            signature_bytes: The signature to verify
            public_key_hex: Hex-encoded public key of the signer

        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Reconstruct the public key from hex encoding
            verify_key = nacl.signing.VerifyKey(
                public_key_hex, encoder=nacl.encoding.HexEncoder
            )

            # Verify the signature
            verify_key.verify(message_bytes, signature_bytes)
            return True

        except nacl.exceptions.BadSignatureError:
            return False
        except Exception as e:
            logger.warning(f"Error verifying signature: {e}")
            return False
