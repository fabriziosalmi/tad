"""
poc-01_discovery.py - TAZCOM PoC Milestone 1: Service Discovery

This module implements a TAZCOM node that:
1. Generates a unique cryptographic identity (Ed25519 key pair)
2. Publishes itself via mDNS/Zeroconf on the local network
3. Discovers other TAZCOM nodes and maintains a peer list
4. Operates asynchronously using Python's asyncio framework

To run: python poc-01_discovery.py
"""

import asyncio
import base64
import json
import logging
import socket
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import nacl.signing
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

# Configure structured logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)-5s] %(message)s",
    datefmt="%H:%M:%S",
)


class TAZCOMNode:
    """
    A TAZCOM network node with cryptographic identity, service publishing,
    and peer discovery via mDNS/Zeroconf.

    Thread Safety:
    - self.peers and self.service_name_to_id are accessed from both the asyncio
      event loop and the Zeroconf callback thread. We use asyncio locks and
      run_coroutine_threadsafe to ensure thread-safe access.
    """

    def __init__(self) -> None:
        """Initialize a new TAZCOM node instance."""
        self.signing_key: nacl.signing.SigningKey
        self.node_id: nacl.signing.VerifyKey
        self.node_id_b64: str
        self.tcp_port: int
        self.local_ip: str
        self.peers: Dict[str, Dict[str, str]] = {}
        # Inverse lookup: maps service_name -> peer_id for O(1) removal
        self.service_name_to_id: Dict[str, str] = {}
        self.aiozc: Optional[AsyncZeroconf] = None
        self.service_browser: Optional[ServiceBrowser] = None
        self.peers_lock: asyncio.Lock = asyncio.Lock()
        # Reference to the event loop for thread-safe operations
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

    def _load_or_create_identity(self) -> None:
        """
        Load an existing node identity from disk, or generate a new one.

        The identity is persisted to 'node.key' as a JSON file containing
        the base64-encoded Ed25519 signing key and creation timestamp.
        Across restarts, this ensures the node maintains the same identity.
        """
        key_file = Path("node.key")

        if key_file.exists():
            # Load existing identity from file
            with open(key_file, "r") as f:
                key_data = json.load(f)
            key_bytes = base64.b64decode(key_data["signing_key"])
            self.signing_key = nacl.signing.SigningKey(key_bytes)
            logger.info(f"Loaded existing identity from {key_file}")
        else:
            # Generate new identity and persist it
            self.signing_key = nacl.signing.SigningKey.generate()
            key_data = {
                "signing_key": base64.b64encode(bytes(self.signing_key)).decode(),
                "created": datetime.now().isoformat(),
            }
            with open(key_file, "w") as f:
                json.dump(key_data, f, indent=2)
            logger.info(f"Generated new identity and saved to {key_file}")

        # Extract the public key (node ID) and encode it for network transmission
        self.node_id = self.signing_key.verify_key
        self.node_id_b64 = (
            base64.urlsafe_b64encode(bytes(self.node_id)).decode().rstrip("=")
        )

    def _find_available_port(self) -> int:
        """
        Find an available TCP port by binding to port 0.

        The OS will assign an unused port, which we retrieve and return.
        This allows multiple nodes to run on the same machine without conflict.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            s.listen(1)
            _, port = s.getsockname()
        return port

    def _get_local_ip(self) -> str:
        """
        Determine the local IP address for this machine.

        Uses a UDP socket connection to a public DNS server (Google's 8.8.8.8)
        to determine the outbound interface, without actually sending data.
        Falls back to localhost if the detection fails.
        """
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def initialize(self) -> None:
        """
        Initialize the node: create/load identity, allocate port, and setup Zeroconf.

        This must be called once before running the node.
        """
        self.event_loop = asyncio.get_event_loop()
        self._load_or_create_identity()
        self.tcp_port = self._find_available_port()
        self.local_ip = self._get_local_ip()

        logger.info("TAZCOM Node Initialized.")
        logger.info(f"Node ID: {self.node_id_b64}")
        logger.info(f"Listening on {self.local_ip}:{self.tcp_port}")

        await self._setup_zeroconf()

    async def _setup_zeroconf(self) -> None:
        """
        Initialize Zeroconf service publishing and discovery.

        1. Creates an AsyncZeroconf instance for IPv4-only operation.
        2. Registers this node as a service on the local network with its
           identity and port in the TXT record.
        3. Sets up a service browser to listen for other TAZCOM nodes
           appearing or disappearing on the network.
        """
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)

        # Build service properties (Zeroconf TXT record)
        properties = {
            "id": self.node_id_b64,  # Full public key ID
            "version": "0.1",  # Protocol version
            "p": str(self.tcp_port),  # TCP port this node listens on
        }

        node_id_short = self.node_id_b64[:8]
        service_name = f"TAZCOM Node {node_id_short}._tazcom._tcp.local."

        # Create and register the service
        info = ServiceInfo(
            "_tazcom._tcp.local.",
            service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.tcp_port,
            properties=properties,
            server=f"tazcom-{node_id_short}.local.",
        )

        await self.aiozc.async_register_service(info)
        logger.info(f"Publishing service '{service_name}'")

        # Start listening for other nodes
        self.service_browser = ServiceBrowser(
            self.aiozc.zeroconf,
            "_tazcom._tcp.local.",
            handlers=[self._on_service_state_change],
        )

    def _on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        """
        Handle Zeroconf service state changes (Added/Removed).

        This callback is invoked synchronously by the ServiceBrowser in a
        separate thread, not in the asyncio event loop. We use
        run_coroutine_threadsafe to safely schedule async operations.
        """
        if self.event_loop is None:
            return

        if state_change == ServiceStateChange.Added:
            asyncio.run_coroutine_threadsafe(
                self._on_service_added(zeroconf, service_type, name), self.event_loop
            )
        elif state_change == ServiceStateChange.Removed:
            asyncio.run_coroutine_threadsafe(
                self._on_service_removed(name), self.event_loop
            )

    async def _on_service_added(
        self, zeroconf: Zeroconf, service_type: str, name: str
    ) -> None:
        """
        Process a newly discovered peer service.

        Retrieves the service info, validates it, and if it's not our own
        service, adds the peer to our peer dictionary and logs the discovery.
        """
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info is None:
                return

            # Extract the peer's ID from TXT records
            properties = info.properties or {}
            peer_id_bytes = properties.get(b"id")
            if not peer_id_bytes:
                return
            peer_id = (
                peer_id_bytes.decode()
                if isinstance(peer_id_bytes, bytes)
                else peer_id_bytes
            )

            # Ignore our own service announcement
            if peer_id == self.node_id_b64:
                return

            # Extract peer network information
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            peer_ip = addresses[0] if addresses else "unknown"
            peer_port = info.port

            # Store peer information with thread-safe lock
            async with self.peers_lock:
                self.peers[peer_id] = {
                    "ip": peer_ip,
                    "port": str(peer_port),
                    "name": name,
                }
                self.service_name_to_id[name] = peer_id

            logger.info(f"Peer Discovered: {peer_id} @ {peer_ip}:{peer_port}")

        except Exception as e:
            logger.warning(f"Error processing service addition: {e}")

    async def _on_service_removed(self, name: str) -> None:
        """
        Process a peer service that has disappeared from the network.

        Uses the inverse lookup table (service_name_to_id) for O(1) removal.
        """
        async with self.peers_lock:
            peer_id = self.service_name_to_id.pop(name, None)
            if peer_id and peer_id in self.peers:
                del self.peers[peer_id]
                logger.info(f"Peer Removed: {peer_id}")

    async def run(self) -> None:
        """
        Run the node indefinitely until interrupted.

        The main loop simply keeps the asyncio event loop running.
        Discovery and service updates happen via callbacks.
        """
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutdown signal received...")
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shut down the node.

        Unregisters the Zeroconf service and closes the AsyncZeroconf instance.
        """
        if self.aiozc:
            await self.aiozc.async_close()
        logger.info("Node shut down successfully.")


async def main() -> None:
    """Main entry point for the PoC node."""
    node = TAZCOMNode()
    await node.initialize()
    await node.run()


if __name__ == "__main__":
    asyncio.run(main())
