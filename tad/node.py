"""
TAD Node - Orchestrator for all network and protocol components

This module provides the TADNode class which manages:
- Cryptographic identity and persistence (via IdentityManager)
- Message persistence (via DatabaseManager - Milestone 4)
- Channel subscriptions (Milestone 3)
- Network service components (Discovery, Connection, Gossip)
- Component lifecycle (start/stop)
- Message routing between components
"""

import asyncio
import logging
import socket
from typing import Callable, Dict, List, Optional, Set, Tuple

import nacl.encoding

from .crypto.e2ee import E2EEManager
from .identity import IdentityManager
from .network.connection import ConnectionManager
from .network.discovery import DiscoveryService
from .network.gossip import GossipProtocol
from .persistence import DatabaseManager

logger = logging.getLogger(__name__)


class TADNode:
    """
    Central orchestrator for a TAD (Temporary Autonomous Devices) node.

    Manages:
    - Identity (Ed25519 key generation and persistence via IdentityManager)
    - Message persistence (SQLite storage via DatabaseManager - Milestone 4)
    - Channel subscriptions (Tribes - Milestone 3)
    - Network services (Discovery, Connections, Gossip Protocol)
    - Lifecycle management (start, stop)
    - Message routing and callbacks
    """

    def __init__(
        self,
        username: str = "DefaultUser",
        db_path: str = "tad_node.db",
        profile_path: str = "profile.json",
        on_message_received: Optional[Callable[[dict], None]] = None,
        on_peer_discovered: Optional[Callable[[str, Tuple[str, int]], None]] = None,
        on_peer_removed: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize a TAD node.

        Args:
            username: Username for this node's identity
            db_path: Path to SQLite database for message persistence (Milestone 4)
            profile_path: Path to the identity profile file (Milestone 6)
            on_message_received: Callback invoked when a message is received
            on_peer_discovered: Callback invoked when a new peer is discovered
            on_peer_removed: Callback invoked when a peer disappears
        """
        self.username = username

        # Identity management
        self.identity_manager = IdentityManager(profile_path=profile_path)
        self.identity = None

        # E2EE and channel key management (Milestone 6)
        self.e2ee_manager = E2EEManager()
        self.channel_keys: Dict[str, bytes] = self.e2ee_manager.channel_keys

        # Database persistence (Milestone 4)
        self.db_manager = DatabaseManager(db_path=db_path)

        # Node identifiers (set during start)
        self.node_id_b64: str = ""

        # Network configuration
        self.tcp_port: int = 0
        self.local_ip: str = ""

        # Channel subscriptions (Milestone 3)
        # Shared with GossipProtocol for local filtering
        self.subscribed_channels: Set[str] = {"#general"}

        # Callbacks
        self.on_message_received = on_message_received
        self.on_peer_discovered = on_peer_discovered
        self.on_peer_removed = on_peer_removed

        # Service instances
        self.connection_manager: Optional[ConnectionManager] = None
        self.gossip_protocol: Optional[GossipProtocol] = None
        self.discovery_service: Optional[DiscoveryService] = None

        # Lifecycle
        self.is_running = False

    async def start(self) -> None:
        """
        Start the TAD node and all its services.

        Order:
        1. Load/create identity (via IdentityManager)
        2. Detect network configuration
        3. Start ConnectionManager (TCP server)
        4. Start GossipProtocol (message signing/forwarding)
        5. Start DiscoveryService (peer discovery)
        """
        logger.info("Starting TAD node...")

        # Load or create identity
        self.identity = self.identity_manager.load_or_create(self.username)
        self.node_id_b64 = self.identity.verify_key_hex
        logger.info(f"Node ID: {self.node_id_b64}")
        logger.info(f"Username: {self.identity.username}")

        # Detect network configuration
        self.tcp_port = self._find_available_port()
        self.local_ip = self._get_local_ip()
        logger.info(f"Node listening on {self.local_ip}:{self.tcp_port}")

        # Create and start ConnectionManager
        self.connection_manager = ConnectionManager(
            self.local_ip,
            self.tcp_port,
            on_message_received=self._on_message_from_peer,
        )
        await self.connection_manager.start()

        # Create and start GossipProtocol (with identity_manager for signing and channels)
        self.gossip_protocol = GossipProtocol(
            node_id_b64=self.node_id_b64,
            connection_manager=self.connection_manager,
            identity_manager=self.identity_manager,
            subscribed_channels=self.subscribed_channels,
            on_message_received=self._on_gossip_message_received,
        )
        await self.gossip_protocol.start()

        # Create and start DiscoveryService
        self.discovery_service = DiscoveryService(
            node_id_b64=self.node_id_b64,
            local_ip=self.local_ip,
            tcp_port=self.tcp_port,
            username=self.username,
            on_peer_found=self._on_peer_discovered,
            on_peer_removed=self._on_peer_removed,
        )
        await self.discovery_service.start()

        self.is_running = True
        logger.info("TAD node started successfully")

    async def stop(self) -> None:
        """
        Stop the TAD node and gracefully shut down all services.

        Order (reverse of start):
        1. Stop DiscoveryService
        2. Stop GossipProtocol
        3. Stop ConnectionManager
        4. Close database connection
        """
        logger.info("Stopping TAD node...")

        self.is_running = False

        if self.discovery_service:
            await self.discovery_service.stop()

        if self.gossip_protocol:
            await self.gossip_protocol.stop()

        if self.connection_manager:
            await self.connection_manager.stop()

        # Close database connection (Milestone 4)
        if self.db_manager:
            self.db_manager.close()

        logger.info("TAD node stopped")

    # ========== Network Configuration ==========

    def _find_available_port(self) -> int:
        """Find an available TCP port by binding to port 0."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            s.listen(1)
            _, port = s.getsockname()
        return port

    def _get_local_ip(self) -> str:
        """Determine the local IP address for this machine."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    # ========== Message Handling ==========

    async def _on_message_from_peer(self, addr: str, message_json: str) -> None:
        """
        Handle a message received from a peer connection.

        Delegates to GossipProtocol for processing with deduplication,
        signature verification, and forwarding.
        """
        if self.gossip_protocol:
            await self.gossip_protocol.handle_message(message_json, addr)

    async def _on_gossip_message_received(self, message: dict) -> None:
        """
        Handle a message after gossip protocol processing (and verification).

        1. Store the message in the database (Milestone 4)
        2. Invoke the user callback if provided
        """
        payload = message.get("payload", {})
        content = payload.get("content")
        channel_id = payload.get("channel_id")

        # Milestone 6: Handle INVITE messages
        if isinstance(content, dict) and content.get("type") == "INVITE":
            if content.get("target_node_id") == self.node_id_b64:
                await self._handle_invite(content)
            return  # Invites are not stored or displayed directly

        # Milestone 6: Decrypt message if it's for a private channel we are in
        if self.e2ee_manager.has_channel_key(channel_id):
            try:
                # 1. Decrypt the content
                decrypted_content = self.e2ee_manager.decrypt_message(
                    self.e2ee_manager.get_channel_key(channel_id),
                    content,  # Ciphertext
                    payload.get("nonce"),  # Nonce
                )

                if decrypted_content is None:
                    logger.warning(
                        f"Could not decrypt message for private channel {channel_id}. Dropping."
                    )
                    return  # Drop message

                # 2. Create a NEW message object for the callback
                #    This prevents modifying the original message dict in place.
                callback_message = message.copy()
                callback_message["payload"]["content"] = decrypted_content
                callback_message["payload"]["is_encrypted"] = True # Add a flag for context

                # 3. Store the ORIGINAL raw message in the database
                self.db_manager.store_message(message)

                # 4. Call the callback with the DECRYPTED message
                if self.on_message_received:
                    # Use asyncio.create_task to avoid blocking the network handler
                    asyncio.create_task(self.on_message_received(callback_message["payload"]))

            except Exception as e:
                logger.warning(f"Failed to decrypt or process message {message.get('msg_id')}: {e}")
                # Do not forward or process a message that cannot be decrypted

        elif self.db_manager.get_channel_info(channel_id) and self.db_manager.get_channel_info(channel_id).get("type") == "private":
            # If it's a private channel but we don't have the key, drop it
            logger.debug(f"Dropping message for private channel {channel_id} (no key).")
            return
        else:
            # Persist message to database (Milestone 4)
            if self.db_manager:
                self.db_manager.store_message(message)

            # Invoke user callback
            if self.on_message_received:
                try:
                    # We need to pass the payload to the callback, not the entire message
                    if asyncio.iscoroutinefunction(self.on_message_received):
                        await self.on_message_received(message["payload"])
                    else:
                        self.on_message_received(message["payload"])
                except Exception as e:
                    logger.warning(f"Error in on_message_received callback: {e}")

    async def _handle_invite(self, invite_payload: dict):
        """
        Process an incoming INVITE for this node.
        """
        channel_id = invite_payload.get("channel_id")
        encrypted_key = invite_payload.get("encrypted_key")
        channel_name = invite_payload.get("channel_name")
        channel_type = invite_payload.get("channel_type")

        # 1. Decrypt the channel key
        channel_key = self.e2ee_manager.decrypt_key_from_sender(
            self.identity.encryption_private_key.encode(encoder=nacl.encoding.HexEncoder).decode(),
            encrypted_key
        )

        if channel_key:
            # 2. Store the key and add membership
            self.e2ee_manager.store_channel_key(channel_id, channel_key)
            self.db_manager.store_channel(
                channel_id,
                name=channel_name,
                channel_type=channel_type,
            )
            self.db_manager.add_channel_member(channel_id, self.node_id_b64)
            self.join_channel(channel_id)

            logger.info(f"Successfully joined private channel {channel_id} via invite.")

            # 3. Notify the UI (optional, requires callback)
            if self.on_message_received:
                system_message = {
                    "payload": {
                        "content": f"[SYSTEM] You have been invited to and joined the private channel {channel_id}",
                        "channel_id": channel_id,
                        "timestamp": "",
                    },
                    "sender_id": "System",
                }
                await self.on_message_received(system_message)

    async def _on_peer_discovered(self, peer_id: str, peer_address: Tuple[str, int]) -> None:
        """
        Handle discovery of a new peer.

        1. Attempt to establish a connection via ConnectionManager
        2. Invoke the user callback if provided
        """
        logger.info(f"Peer discovered: {peer_id} @ {peer_address}")

        # Try to connect to the new peer
        if self.connection_manager:
            await self.connection_manager.connect_to_peer(peer_id, peer_address)

        # Invoke the user callback
        if self.on_peer_discovered:
            try:
                if asyncio.iscoroutinefunction(self.on_peer_discovered):
                    await self.on_peer_discovered(peer_id, peer_address)
                else:
                    self.on_peer_discovered(peer_id, peer_address)
            except Exception as e:
                logger.warning(f"Error in on_peer_discovered callback: {e}")

    async def _on_peer_removed(self, peer_id: str) -> None:
        """Handle removal of a peer from the network."""
        logger.info(f"Peer removed: {peer_id}")

        if self.on_peer_removed:
            try:
                if asyncio.iscoroutinefunction(self.on_peer_removed):
                    await self.on_peer_removed(peer_id)
                else:
                    self.on_peer_removed(peer_id)
            except Exception as e:
                logger.warning(f"Error in on_peer_removed callback: {e}")

    # ========== Channel Management (Milestone 3) ==========

    def join_channel(self, channel_id: str) -> None:
        """
        Subscribe to a channel to receive messages sent to that channel.

        Args:
            channel_id: Channel identifier (e.g., "#general", "#dev", "#offtopic")
        """
        if channel_id not in self.subscribed_channels:
            self.subscribed_channels.add(channel_id)
            logger.info(f"Joined channel: {channel_id}")
        else:
            logger.debug(f"Already subscribed to channel: {channel_id}")

    def leave_channel(self, channel_id: str) -> None:
        """
        Unsubscribe from a channel to stop receiving messages from that channel.

        Args:
            channel_id: Channel identifier to leave
        """
        if channel_id in self.subscribed_channels:
            self.subscribed_channels.discard(channel_id)
            logger.info(f"Left channel: {channel_id}")
        else:
            logger.debug(f"Not subscribed to channel: {channel_id}")

    def get_subscribed_channels(self) -> Set[str]:
        """
        Get the set of channels this node is currently subscribed to.

        Returns:
            Set of channel IDs
        """
        return self.subscribed_channels.copy()

    # ========== Secure Channel Management (Milestone 6) ==========

    def create_channel(self, channel_id: str, channel_type: str = "public") -> bool:
        """
        Create a new channel, public or private.

        Args:
            channel_id: The ID of the channel (e.g., "#private-chat").
            channel_type: 'public' or 'private'.

        Returns:
            True if creation was successful, False otherwise.
        """
        if self.db_manager.get_channel_info(channel_id):
            logger.warning(f"Channel {channel_id} already exists.")
            return False

        owner_node_id = None
        if channel_type == "private":
            # 1. Generate and store a new symmetric key
            key = self.e2ee_manager.generate_channel_key()
            self.e2ee_manager.store_channel_key(channel_id, key)
            owner_node_id = self.node_id_b64
            logger.info(f"Created private channel {channel_id} with new key.")

        # 2. Persist channel and owner's membership
        self.db_manager.store_channel(
            channel_id,
            name=channel_id,
            channel_type=channel_type,
            owner_node_id=owner_node_id,
        )
        self.db_manager.add_channel_member(
            channel_id, self.node_id_b64, role="owner"
        )

        # 3. Join the channel
        self.join_channel(channel_id)
        return True

    async def invite_peer_to_channel(self, channel_id: str, target_node_id: str, target_public_key_hex: str):
        """
        Invite a peer to a private channel by sending them the channel key,
        encrypted with their public key.
        """
        # 1. Check if current node is the owner
        channel_info = self.db_manager.get_channel_info(channel_id)
        if not channel_info or channel_info["owner_node_id"] != self.node_id_b64:
            logger.warning(f"Only the owner can invite peers to {channel_id}.")
            return

        # 2. Retrieve the symmetric channel_key
        channel_key = self.e2ee_manager.get_channel_key(channel_id)
        if not channel_key:
            logger.error(f"Missing key for owned private channel {channel_id}.")
            return

        # 4. Encrypt the channel_key using SealedBox
        encrypted_key = self.e2ee_manager.encrypt_key_for_recipient(
            target_public_key_hex, channel_key
        )

        # 5. Create and broadcast an INVITE message
        invite_payload = {
            "type": "INVITE",
            "channel_id": channel_id,
            "channel_name": channel_info["name"],
            "channel_type": channel_info["type"],
            "target_node_id": target_node_id,
            "encrypted_key": encrypted_key,
        }
        if self.gossip_protocol:
            await self.gossip_protocol.broadcast_message(
                content=invite_payload, channel_id="#general"  # Invites are public
            )
            logger.info(f"Sent invite for {channel_id} to {target_node_id[:8]}...")

    # ========== Message History (Milestone 4) ==========

    async def load_channel_history(
        self, channel_id: str, last_n: int = 50
    ) -> List[Dict]:
        """
        Load message history for a channel from persistent storage.

        Used during UI initialization to pre-populate message view with historical messages
        before displaying real-time messages.

        Args:
            channel_id: Channel to load history for
            last_n: Number of recent messages to load (default: 50)

        Returns:
            List of message dictionaries from database
        """
        if not self.db_manager:
            return []

        logger.info(f"Loading history for {channel_id} (last {last_n} messages)")
        messages = self.db_manager.get_messages_for_channel(
            channel_id, last_n=last_n
        )

        # Milestone 6: Decrypt messages if channel is private
        if self.e2ee_manager.has_channel_key(channel_id):
            decrypted_messages = []
            channel_key = self.e2ee_manager.get_channel_key(channel_id)

            for msg in messages:
                # Ensure payload is a dictionary
                try:
                    payload = (
                        msg["payload"]
                        if isinstance(msg["payload"], dict)
                        else json.loads(msg["payload"])
                    )
                except (json.JSONDecodeError, TypeError):
                    payload = {"content": msg.get("content", "")}

                if payload.get("is_encrypted"):
                    decrypted_content = self.e2ee_manager.decrypt_message(
                        channel_key, payload["content"], payload["nonce"]
                    )
                    if decrypted_content is not None:
                        payload["content"] = decrypted_content
                        msg["payload"] = payload
                        decrypted_messages.append(msg)
                    # else: message is dropped
                else:
                    decrypted_messages.append(msg)
            messages = decrypted_messages

        logger.info(f"Loaded {len(messages)} historical messages for {channel_id}")

        return messages

    def get_database_stats(self) -> Dict:
        """
        Get database statistics for monitoring and debugging.

        Returns:
            Dictionary containing message counts and storage info
        """
        if not self.db_manager:
            return {}

        return self.db_manager.get_database_stats()

    # ========== Public API ==========

    async def broadcast_message(
        self, content: str, channel_id: str = "#general"
    ) -> str:
        """
        Broadcast a message to a specific channel.

        Uses the gossip protocol for multi-hop delivery with automatic signing.
        Only node subscribed to the channel will process the message.

        Args:
            content: The message content
            channel_id: Target channel for the message (default: "#general")

        Returns:
            The generated msg_id
        """
        if not self.gossip_protocol:
            logger.warning("Gossip protocol not initialized")
            return ""

        extra_payload = {}
        # Milestone 6: Encrypt message if sending to a private channel
        if self.e2ee_manager.has_channel_key(channel_id):
            channel_key = self.e2ee_manager.get_channel_key(channel_id)
            ciphertext, nonce = self.e2ee_manager.encrypt_message(channel_key, content)

            # Replace original content with ciphertext
            content = ciphertext
            extra_payload["nonce"] = nonce
            extra_payload["is_encrypted"] = True

        return await self.gossip_protocol.broadcast_message(
            content, channel_id, extra_payload=extra_payload
        )

    async def get_connected_peers(self) -> list:
        """Get list of currently connected peer addresses."""
        if not self.connection_manager:
            return []

        return await self.connection_manager.get_connected_peers()

    def get_node_info(self) -> dict:
        """Get information about this node."""
        return {
            "username": self.username,
            "node_id": self.node_id_b64,
            "ip": self.local_ip,
            "port": self.tcp_port,
            "is_running": self.is_running,
        }

    def get_identity_info(self) -> dict:
        """Get information about this node's identity."""
        if not self.identity:
            return {}

        return {
            "username": self.identity.username,
            "public_key": self.identity.verify_key_hex,
        }

    def get_gossip_stats(self) -> dict:
        """Get gossip protocol statistics."""
        if not self.gossip_protocol:
            return {}

        return {
            "seen_messages_count": self.gossip_protocol.get_seen_messages_count(),
            "cache_utilization": self.gossip_protocol.get_cache_utilization(),
        }