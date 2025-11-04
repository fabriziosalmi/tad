"""
TAD Gossip Protocol with Message Signing and Channel Support

Implements the gossip protocol for multi-hop mesh message delivery:
- Message signing with Ed25519 digital signatures
- Signature verification for received messages
- Channel-based message filtering (Milestone 3)
- Message deduplication via unique msg_id
- TTL-based hop limiting
- Automatic message forwarding through the network
- Circular buffer cache for seen messages
"""

import asyncio
import hashlib
import json
import logging
from collections import deque
from datetime import datetime
from typing import Callable, Dict, Optional, Set, Tuple

import nacl.encoding
import nacl.exceptions

logger = logging.getLogger(__name__)


class GossipProtocol:
    """
    Implements the gossip protocol for mesh networking with cryptographic signing and channels.

    Features:
    - Message signing and verification (Ed25519)
    - Channel subscriptions with local filtering (Milestone 3)
    - Message deduplication via msg_id
    - TTL-based multi-hop forwarding
    - Circular buffer cache for tracking seen messages
    - Automatic forwarding of messages through peer network
    """

    # Protocol constants
    INITIAL_TTL = 3  # How many hops before message expires
    SEEN_MESSAGES_MAX_SIZE = 1000  # Circular buffer size

    def __init__(
        self,
        node_id_b64: str,
        connection_manager,
        identity_manager,
        subscribed_channels: Set[str],
        on_message_received: Callable[[Dict], None],
    ):
        """
        Initialize the GossipProtocol.

        Args:
            node_id_b64: Node identifier (public key hex)
            connection_manager: Instance of ConnectionManager for sending messages
            identity_manager: Instance of IdentityManager for signing/verifying
            subscribed_channels: Set of channel IDs this node is subscribed to (shared ref)
            on_message_received: Callback invoked when a valid message is received.
                               Should accept (message_dict)
        """
        self.node_id_b64 = node_id_b64
        self.connection_manager = connection_manager
        self.identity_manager = identity_manager
        self.subscribed_channels = subscribed_channels  # Shared reference for dynamic updates
        self.on_message_received = on_message_received

        # Seen messages cache (circular buffer to prevent loops)
        self.seen_messages: deque = deque(maxlen=self.SEEN_MESSAGES_MAX_SIZE)

        # Track active message listening tasks
        self.listening_tasks: set = set()

    async def start(self) -> None:
        """
        Start the gossip protocol (initialize the deque).

        In the future, this could start background tasks for message management.
        """
        logger.info("GossipProtocol started")

    async def stop(self) -> None:
        """
        Stop the gossip protocol and cancel active tasks.
        """
        for task in self.listening_tasks:
            task.cancel()

        self.listening_tasks.clear()
        logger.info("GossipProtocol stopped")

    # ========== Message Signing ==========

    def sign_message(self, payload: Dict) -> Dict:
        """
        Sign a message payload with the node's private key.

        The message envelope includes the sender ID and signature, allowing
        recipients to verify the authenticity of the message.

        Args:
            payload: Dictionary containing message data (type, content, timestamp, etc.)

        Returns:
            Signed message envelope with structure:
            {
                "msg_id": "unique_hash",
                "payload": {...},
                "sender_id": "hex_encoded_public_key",
                "signature": "hex_encoded_signature"
            }

        Raises:
            RuntimeError: If identity is not loaded
        """
        identity = self.identity_manager.get_identity()
        if not identity:
            raise RuntimeError("Identity not loaded. Cannot sign messages.")

        # Serialize payload with deterministic JSON ordering for consistent signatures
        payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        payload_bytes = payload_json.encode("utf-8")

        # Sign the payload
        signature_bytes = self.identity_manager.sign_data(payload_bytes)

        # Generate unique message ID
        msg_id_input = f"{payload_json}:{datetime.now().isoformat()}:{identity.verify_key_hex}"
        msg_id = hashlib.sha256(msg_id_input.encode()).hexdigest()[:16]

        # Get sender's public key in hex format
        sender_id = identity.verify_key_hex

        # Encode signature as hex for transmission
        signature_hex = signature_bytes.hex()

        # Return signed message envelope
        signed_message = {
            "msg_id": msg_id,
            "payload": payload,
            "sender_id": sender_id,
            "signature": signature_hex,
        }

        logger.debug(f"Message signed with msg_id: {msg_id}")
        return signed_message

    def verify_message(self, message: Dict) -> Tuple[bool, Optional[str]]:
        """
        Verify the signature of a received message.

        Args:
            message: Signed message envelope to verify

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
            - If valid: (True, None)
            - If invalid: (False, error_description)
        """
        try:
            # Extract message components
            payload = message.get("payload")
            sender_id = message.get("sender_id")
            signature_hex = message.get("signature")
            msg_id = message.get("msg_id")

            # Validate all required fields are present
            if not all([payload, sender_id, signature_hex, msg_id]):
                return False, "Message missing required fields"

            # Reconstruct the payload bytes (must match exactly how it was signed)
            payload_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            payload_bytes = payload_json.encode("utf-8")

            # Convert signature from hex back to bytes
            try:
                signature_bytes = bytes.fromhex(signature_hex)
            except ValueError:
                return False, "Invalid signature encoding (not valid hex)"

            # Verify the signature using the sender's public key
            is_valid = self.identity_manager.verify_signature(
                payload_bytes, signature_bytes, sender_id
            )

            if is_valid:
                logger.debug(f"Message {msg_id} signature verified")
                return True, None
            else:
                return False, "Signature verification failed"

        except Exception as e:
            logger.warning(f"Error verifying message: {e}")
            return False, str(e)

    # ========== Message Handling ==========

    async def handle_message(self, message_json: str, sender_addr: str) -> None:
        """
        Handle an incoming message with gossip logic and channel filtering.

        1. Parse the message
        2. Verify the signature (discard if invalid)
        3. Check channel subscription (CRITICAL: discard if not subscribed - Milestone 3)
        4. Check for duplicates (msg_id)
        5. If duplicate, ignore
        6. If new, add to seen_messages and invoke callback
        7. If ttl > 0, forward to other peers

        Args:
            message_json: JSON string of the signed message
            sender_addr: Address of the sender ("ip:port")
        """
        try:
            message = json.loads(message_json)
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from {sender_addr}: {message_json[:50]}")
            return

        # Verify the message signature
        is_valid, error_msg = self.verify_message(message)
        if not is_valid:
            logger.warning(
                f"Message signature verification failed from {sender_addr}: {error_msg}"
            )
            return

        # Extract payload (contains actual message data)
        payload = message.get("payload", {})
        msg_type = payload.get("type")
        msg_id = message.get("msg_id")

        # MILESTONE 3: Extract channel_id and filter early
        channel_id = payload.get("channel_id")

        if not msg_type or not msg_id:
            logger.warning(f"Message missing type or msg_id from {sender_addr}")
            return

        # MILESTONE 3: CRITICAL FILTERING STEP
        # If the channel_id is not in our subscribed_channels, discard COMPLETELY:
        # - Don't add to seen_messages (allows re-receipt if we later subscribe)
        # - Don't invoke callback
        # - Don't forward to other peers
        if channel_id and channel_id not in self.subscribed_channels:
            logger.debug(
                f"Ignoring message {msg_id} for channel '{channel_id}' "
                f"(not subscribed; subscribed to: {self.subscribed_channels})"
            )
            return

        # Handle different message types (only for subscribed channels)
        if msg_type == "chat_message":
            await self._handle_chat_message(message, payload, sender_addr)
        elif msg_type == "HELLO":
            await self._handle_hello_message(message, payload, sender_addr)
        else:
            logger.debug(f"Unknown message type: {msg_type}")

    async def _handle_chat_message(
        self, message: Dict, payload: Dict, sender_addr: str
    ) -> None:
        """
        Handle a chat_message with deduplication and forwarding.
        Messages are only processed if the channel is subscribed.
        """
        msg_id = message.get("msg_id")
        sender_id = message.get("sender_id", "unknown")[:8]
        channel_id = payload.get("channel_id", "unknown")

        # Check if we've seen this message before
        if msg_id in self.seen_messages:
            logger.debug(f"Duplicate message {msg_id} from {sender_addr}")
            return

        # New message: add to seen_messages and process
        self.seen_messages.append(msg_id)
        logger.info(f"New message {msg_id} in channel '{channel_id}' from {sender_id} via {sender_addr}")

        # Invoke the callback for UI display, etc.
        try:
            await self.on_message_received(message)
        except Exception as e:
            logger.warning(f"Error processing message callback: {e}")

        # Forward to other peers if TTL allows
        ttl = message.get("ttl", 0)
        if ttl > 0:
            await self.forward_message(message)

    async def _handle_hello_message(
        self, message: Dict, payload: Dict, sender_addr: str
    ) -> None:
        """
        Handle a HELLO message (peer greeting).

        For now, just log it. Future versions might maintain peer state.
        """
        sender_id = message.get("sender_id", "unknown")[:8]
        logger.info(f"HELLO from {sender_id} @ {sender_addr}")

    # ========== Message Forwarding ==========

    async def forward_message(self, message: Dict) -> None:
        """
        Forward a message to all connected peers with TTL decremented.

        Args:
            message: The signed message to forward
        """
        payload = message.get("payload", {})
        ttl = payload.get("ttl", 0)

        # Decrement TTL
        new_ttl = ttl - 1

        # If TTL exhausted, don't forward
        if new_ttl <= 0:
            logger.debug(f"TTL exhausted for message {message.get('msg_id')}")
            return

        # Create a copy with new TTL
        forwarded_msg = message.copy()
        forwarded_payload = payload.copy()
        forwarded_payload["ttl"] = new_ttl
        forwarded_msg["payload"] = forwarded_payload

        # Send to all connected peers
        peers = await self.connection_manager.get_connected_peers()
        logger.debug(f"Forwarding message {message.get('msg_id')} to {len(peers)} peers")

        for addr in peers:
            asyncio.create_task(self._forward_to_peer(addr, forwarded_msg))

    async def _forward_to_peer(self, addr: str, message: Dict) -> None:
        """
        Forward a message to a specific peer.

        Args:
            addr: Address key "ip:port"
            message: The message to send
        """
        try:
            success = await self.connection_manager.send_message(addr, message)
            if success:
                logger.debug(f"Forwarded message {message.get('msg_id')} to {addr}")
        except Exception as e:
            logger.debug(f"Error forwarding to {addr}: {e}")

    # ========== Broadcasting ==========

    async def broadcast_message(
        self, content: str, channel_id: str = "#general", extra_payload: Dict = None
    ) -> str:
        """
        Broadcast a message to a specific channel with automatic signing.

        Creates a new message, signs it with the node's private key, and sends
        it to all connected peers via the gossip protocol. Only peers subscribed
        to the channel will process the message.

        Args:
            content: The message content
            channel_id: Target channel identifier (default: "#general")
            extra_payload: Optional dictionary to merge into the payload

        Returns:
            The generated msg_id
        """
        if isinstance(content, dict):
            pass  # content is already a dict, no need to strip
        elif not content.strip():
            logger.warning("Ignoring empty message content")
            return ""

        # Create the payload (unsigned message data) with channel_id
        # This payload will be signed, so channel_id becomes part of the signature
        timestamp = datetime.now().isoformat()
        payload = {
            "channel_id": channel_id,  # MILESTONE 3: Add channel to payload
            "type": "chat_message",    # Updated message type name
            "content": content,
            "timestamp": timestamp,
        }

        if extra_payload:
            payload.update(extra_payload)

        # Sign the message (signature covers the channel_id in payload)
        signed_message = self.sign_message(payload)
        msg_id = signed_message["msg_id"]

        # Add TTL outside the payload (not signed, can change during forwarding)
        signed_message["ttl"] = self.INITIAL_TTL

        # Add to seen messages immediately
        self.seen_messages.append(msg_id)

        # Broadcast to all connected peers
        peer_count = await self.connection_manager.broadcast_message(signed_message)
        logger.info(f"Broadcast message {msg_id} to {peer_count} peers on channel '{channel_id}'")

        # Also invoke callback so message appears in UI
        try:
            await self.on_message_received(signed_message)
        except Exception as e:
            logger.warning(f"Error processing broadcast callback: {e}")

        return msg_id

    # ========== Statistics ==========

    def get_seen_messages_count(self) -> int:
        """Get count of messages in the seen cache."""
        return len(self.seen_messages)

    def get_cache_utilization(self) -> float:
        """Get cache utilization percentage."""
        return (len(self.seen_messages) / self.SEEN_MESSAGES_MAX_SIZE) * 100
