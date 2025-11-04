"""
TAD Network Connection Manager

This module manages TCP connections with peer nodes:
- Running a TCP server to receive incoming connections
- Establishing TCP connections to discovered peers
- Sending and receiving JSON-formatted messages
- Maintaining active connections for efficient communication
"""

import asyncio
import json
import logging
from typing import Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages TCP connections with peer nodes.

    - Runs a TCP server listening for incoming connections
    - Maintains a list of StreamWriter objects for active peer connections
    - Handles incoming messages from peers via callbacks
    - Provides methods to send messages to peers
    """

    # Message protocol constants
    MESSAGE_ENCODING = "utf-8"
    MESSAGE_TERMINATOR = b"\n"
    MESSAGE_SIZE_LIMIT = 4096

    def __init__(
        self,
        host: str,
        port: int,
        on_message_received: Callable[[str, str], None],
    ):
        """
        Initialize the ConnectionManager.

        Args:
            host: IP address to bind the server to
            port: TCP port to bind the server to
            on_message_received: Callback invoked when a message is received.
                               Should accept (peer_address, message_json)
        """
        self.host = host
        self.port = port
        self.on_message_received = on_message_received

        self.server: Optional[asyncio.Server] = None
        self.peer_writers: Dict[str, asyncio.StreamWriter] = {}  # addr -> writer
        self.peer_lock = asyncio.Lock()
        self.active_connections: set = set()  # Track all active connection tasks

    async def start(self) -> None:
        """
        Start the TCP server and begin listening for incoming connections.
        """
        self.server = await asyncio.start_server(
            self._handle_incoming_connection,
            self.host,
            self.port,
        )
        logger.info(f"ConnectionManager server started on {self.host}:{self.port}")

    async def stop(self) -> None:
        """
        Stop the server and close all active connections.
        """
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            logger.info("ConnectionManager server stopped")

        # Close all peer connections
        async with self.peer_lock:
            for addr, writer in list(self.peer_writers.items()):
                try:
                    writer.close()
                    await writer.wait_closed()
                except Exception:
                    pass
            self.peer_writers.clear()

        # Cancel all active connection tasks
        for task in self.active_connections:
            task.cancel()

    async def connect_to_peer(self, peer_id: str, peer_address: Tuple[str, int]) -> bool:
        """
        Establish a TCP connection to a peer and keep it alive.

        Args:
            peer_id: Identifier for the peer (used for tracking)
            peer_address: Tuple of (ip, port)

        Returns:
            True if connection established successfully, False otherwise
        """
        ip, port = peer_address

        try:
            # Check if we already have a connection to this peer
            addr_key = f"{ip}:{port}"
            async with self.peer_lock:
                if addr_key in self.peer_writers:
                    logger.info(f"Already connected to {addr_key}")
                    return True

            # Attempt to connect
            try:
                reader, writer = await asyncio.wait_for(
                    asyncio.open_connection(ip, port), timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning(f"Connection timeout to {addr_key}")
                return False

            # Store the writer for later use
            async with self.peer_lock:
                self.peer_writers[addr_key] = writer

            logger.info(f"Connected to peer {peer_id} @ {addr_key}")

            # Start listening for messages from this peer in the background
            task = asyncio.create_task(self._listen_to_peer(reader, writer, addr_key))
            self.active_connections.add(task)
            task.add_done_callback(self.active_connections.discard)

            return True

        except ConnectionRefusedError:
            logger.warning(f"Connection refused by {ip}:{port}")
            return False
        except Exception as e:
            logger.warning(f"Error connecting to {ip}:{port}: {e}")
            return False

    async def _handle_incoming_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        """
        Handle an incoming TCP connection from a peer.

        Reads messages and invokes the callback for each message received.
        """
        addr = writer.get_extra_info("peername")
        addr_key = f"{addr[0]}:{addr[1]}"

        try:
            while True:
                # Read a message (up to newline)
                data = await asyncio.wait_for(
                    reader.readuntil(self.MESSAGE_TERMINATOR), timeout=30.0
                )

                if not data:
                    break

                message = data.decode(self.MESSAGE_ENCODING).strip()
                logger.debug(f"Received from {addr_key}: {message}")

                # Invoke the callback
                try:
                    await self.on_message_received(addr_key, message)
                except Exception as e:
                    logger.warning(f"Error processing message from {addr_key}: {e}")

                # Send acknowledgment
                ack_response = b"ACK\n"
                writer.write(ack_response)
                await writer.drain()

        except asyncio.TimeoutError:
            logger.info(f"Connection timeout from {addr_key}")
        except asyncio.LimitOverrunError:
            logger.warning(f"Message from {addr_key} exceeds size limit")
        except Exception as e:
            logger.debug(f"Connection closed from {addr_key}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

            # Remove from peer writers if it was stored
            async with self.peer_lock:
                if addr_key in self.peer_writers:
                    del self.peer_writers[addr_key]

    async def _listen_to_peer(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        addr_key: str,
    ) -> None:
        """
        Listen for messages from an outbound peer connection.

        Reads messages and invokes the callback for each message received.
        """
        try:
            while True:
                data = await asyncio.wait_for(
                    reader.readuntil(self.MESSAGE_TERMINATOR), timeout=30.0
                )

                if not data:
                    break

                message = data.decode(self.MESSAGE_ENCODING).strip()
                logger.debug(f"Received from {addr_key}: {message}")

                # Invoke the callback
                try:
                    await self.on_message_received(addr_key, message)
                except Exception as e:
                    logger.warning(f"Error processing message from {addr_key}: {e}")

        except asyncio.TimeoutError:
            logger.debug(f"Peer {addr_key} timeout")
        except asyncio.CancelledError:
            logger.debug(f"Peer {addr_key} connection cancelled")
        except Exception as e:
            logger.debug(f"Peer {addr_key} disconnected: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

            # Remove from peer writers
            async with self.peer_lock:
                if addr_key in self.peer_writers:
                    del self.peer_writers[addr_key]

            logger.info(f"Disconnected from {addr_key}")

    async def send_message(self, addr_key: str, message: dict) -> bool:
        """
        Send a JSON message to a peer.

        Args:
            addr_key: Address key "ip:port"
            message: Dictionary to be serialized as JSON

        Returns:
            True if message sent successfully, False otherwise
        """
        async with self.peer_lock:
            writer = self.peer_writers.get(addr_key)
            if not writer:
                logger.warning(f"No connection to {addr_key}")
                return False

        try:
            message_json = json.dumps(message)
            message_bytes = (message_json + "\n").encode(self.MESSAGE_ENCODING)

            writer.write(message_bytes)
            await writer.drain()

            logger.debug(f"Sent message to {addr_key}")
            return True

        except Exception as e:
            logger.warning(f"Error sending message to {addr_key}: {e}")
            return False

    async def broadcast_message(self, message: dict) -> int:
        """
        Send a message to all connected peers.

        Args:
            message: Dictionary to be serialized as JSON

        Returns:
            Number of peers the message was successfully sent to
        """
        async with self.peer_lock:
            addresses = list(self.peer_writers.keys())

        success_count = 0
        for addr in addresses:
            if await self.send_message(addr, message):
                success_count += 1

        logger.info(f"Broadcast message sent to {success_count}/{len(addresses)} peers")
        return success_count

    def get_active_writers(self) -> Dict[str, asyncio.StreamWriter]:
        """
        Get a copy of all active peer writers.

        Returns:
            Dictionary mapping address keys to StreamWriter objects
        """
        # Note: This is a snapshot, not a live reference
        return dict(self.peer_writers)

    async def get_connected_peers(self) -> List[str]:
        """
        Get list of currently connected peer addresses.

        Returns:
            List of "ip:port" address strings
        """
        async with self.peer_lock:
            return list(self.peer_writers.keys())
