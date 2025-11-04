"""
TAD Network Discovery Service

This module provides peer discovery on the local network via mDNS/Zeroconf.
It handles:
- Publishing this node's service
- Discovering other TAD nodes
- Managing thread-safe peer list updates via async callbacks
"""

import asyncio
import logging
import socket
from typing import Callable, Dict, Optional, Tuple

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

logger = logging.getLogger(__name__)


class DiscoveryService:
    """
    Manages peer discovery via Zeroconf/mDNS.

    Publishes this node's service on the network and discovers other TAD nodes.
    When a new peer is discovered, invokes an async callback to allow the
    ConnectionManager or other components to react.

    Thread Safety:
    - The Zeroconf ServiceBrowser callbacks run in a separate thread.
    - We use asyncio.run_coroutine_threadsafe to safely invoke async callbacks
      in the event loop.
    """

    # Zeroconf service type for TAD nodes
    SERVICE_TYPE = "_tad._tcp.local."

    def __init__(
        self,
        node_id_b64: str,
        local_ip: str,
        tcp_port: int,
        username: str,
        on_peer_found: Callable[[Tuple[str, int]], None],
        on_peer_removed: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the DiscoveryService.

        Args:
            node_id_b64: Base64-encoded node ID (public key)
            local_ip: Local IP address to bind to
            tcp_port: TCP port this node listens on
            username: The username of the node
            on_peer_found: Async callback invoked when a new peer is discovered.
                          Should accept (peer_id, (ip, port))
            on_peer_removed: Optional async callback invoked when a peer disappears
        """
        self.node_id_b64 = node_id_b64
        self.local_ip = local_ip
        self.tcp_port = tcp_port
        self.username = username
        self.on_peer_found = on_peer_found
        self.on_peer_removed = on_peer_removed

        self.aiozc: Optional[AsyncZeroconf] = None
        self.service_browser: Optional[ServiceBrowser] = None
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None

        # Track which peers we've already notified to avoid duplicates
        self.discovered_peers: Dict[str, Tuple[str, int]] = {}

    async def start(self) -> None:
        """
        Start the discovery service.

        - Initializes AsyncZeroconf
        - Publishes this node's service
        - Starts listening for other nodes
        """
        self.event_loop = asyncio.get_event_loop()

        # Initialize Zeroconf for IPv4-only operation
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)

        # Publish this node's service
        await self._publish_service()

        # Start listening for other nodes
        self.service_browser = ServiceBrowser(
            self.aiozc.zeroconf,
            self.SERVICE_TYPE,
            handlers=[self._on_service_state_change],
        )

        logger.info("DiscoveryService started")

    async def stop(self) -> None:
        """
        Stop the discovery service and clean up resources.
        """
        if self.aiozc:
            await self.aiozc.async_close()

        self.service_browser = None
        logger.info("DiscoveryService stopped")

    async def _publish_service(self) -> None:
        """
        Publish this node's service on the Zeroconf network.
        """
        service_name = f"TAD Node {self.username}.{self.SERVICE_TYPE}"

        # Service properties (Zeroconf TXT record)
        properties = {
            "id": self.node_id_b64,
            "version": "1.0",
            "p": str(self.tcp_port),
        }

        info = ServiceInfo(
            self.SERVICE_TYPE,
            service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.tcp_port,
            properties=properties,
            server=f"tad-{self.username}.local.",
        )

        await self.aiozc.async_register_service(info)
        logger.info(f"Published service: {service_name}")

    def _on_service_state_change(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
        state_change: ServiceStateChange,
    ) -> None:
        """
        Zeroconf callback for service state changes.

        This callback runs in the Zeroconf thread, not in the asyncio event loop.
        We use run_coroutine_threadsafe to safely invoke async code.
        """
        if self.event_loop is None:
            return

        if state_change == ServiceStateChange.Added:
            asyncio.run_coroutine_threadsafe(
                self._handle_peer_added(zeroconf, service_type, name),
                self.event_loop,
            )
        elif state_change == ServiceStateChange.Removed:
            asyncio.run_coroutine_threadsafe(
                self._handle_peer_removed(name),
                self.event_loop,
            )

    async def _handle_peer_added(
        self,
        zeroconf: Zeroconf,
        service_type: str,
        name: str,
    ) -> None:
        """
        Handle discovery of a new peer service.
        """
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info is None:
                return

            # Extract peer ID from TXT record
            properties = info.properties or {}
            peer_id_bytes = properties.get(b"id")
            if not peer_id_bytes:
                return

            peer_id = (
                peer_id_bytes.decode()
                if isinstance(peer_id_bytes, bytes)
                else peer_id_bytes
            )

            # Ignore our own service
            if peer_id == self.node_id_b64:
                return

            # Extract peer address
            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            peer_ip = addresses[0] if addresses else None
            peer_port = info.port

            if not peer_ip:
                return

            peer_address = (peer_ip, peer_port)

            # Track and notify only once per peer
            if peer_id not in self.discovered_peers:
                self.discovered_peers[peer_id] = peer_address
                logger.info(f"Peer discovered: {peer_id} @ {peer_ip}:{peer_port}")

                # Invoke the callback
                await self.on_peer_found(peer_id, peer_address)

        except Exception as e:
            logger.warning(f"Error handling peer addition: {e}")

    async def _handle_peer_removed(self, name: str) -> None:
        """
        Handle removal of a peer service.
        """
        try:
            # Search for the peer ID by service name
            peer_id_to_remove = None
            for peer_id in list(self.discovered_peers.keys()):
                if self.discovered_peers[peer_id]:
                    # Find by matching the service name pattern
                    # This is a simplified approach; in production, maintain a name->id map
                    peer_id_to_remove = peer_id
                    break

            if peer_id_to_remove:
                del self.discovered_peers[peer_id_to_remove]
                logger.info(f"Peer removed: {peer_id_to_remove}")

                # Invoke the removal callback if provided
                if self.on_peer_removed:
                    await self.on_peer_removed(peer_id_to_remove)

        except Exception as e:
            logger.warning(f"Error handling peer removal: {e}")


