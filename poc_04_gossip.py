"""
poc-04_gossip.py - TAZCOM PoC Milestone 4: Gossip Protocol (Mesh Networking)

This extends poc-03_chat_basic.py with a gossip protocol for multi-hop message delivery.

Key Features:
1. Messages have unique msg_id for duplicate detection
2. Messages have ttl (time-to-live) for hop limiting
3. Nodes automatically forward messages through the mesh
4. Duplicate messages are ignored (prevents loops)
5. Original sender information is preserved across hops

This enables true mesh networking where:
- Node A sends a message with ttl=3
- Node B (neighbor of A) receives it, decrements ttl to 2, forwards to Node C
- Node C (neighbor of B, but not A) receives it, decrements ttl to 1, forwards to Node D
- Messages propagate through the entire network regardless of direct connections

To run:
    python poc-04_gossip.py

Then open multiple terminals and run the same command.
The network will automatically relay messages across hops.

Controls:
    Type message + Enter: Send to all peers (and through mesh)
    Ctrl+C: Quit gracefully
"""

import asyncio
import base64
import hashlib
import json
import logging
import socket
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

import nacl.signing
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Input, RichLog, Static
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)-5s] %(message)s",
)


class TAZCOMNodeGossip:
    """
    TAZCOM network node with Gossip Protocol support.

    Extends TAZCOMNode with:
    - Message deduplication via msg_id
    - TTL-based message forwarding
    - Multi-hop mesh delivery
    """

    # Message protocol constants
    MESSAGE_ENCODING = "utf-8"
    MESSAGE_TERMINATOR = b"\n"
    MESSAGE_SIZE_LIMIT = 1024

    # Gossip protocol constants
    INITIAL_TTL = 3  # How many hops a message can make
    SEEN_MESSAGES_MAX_SIZE = 1000  # Max messages to track (circular buffer)

    def __init__(self, app: "TAZCOMChatAppGossip") -> None:
        """
        Initialize a TAZCOM node with Gossip Protocol.

        Args:
            app: Reference to the Textual app instance.
        """
        self.app = app
        self.signing_key: nacl.signing.SigningKey
        self.node_id: nacl.signing.VerifyKey
        self.node_id_b64: str
        self.tcp_port: int
        self.local_ip: str
        self.peers: Dict[str, Dict[str, str]] = {}
        self.service_name_to_id: Dict[str, str] = {}
        self.aiozc: Optional[AsyncZeroconf] = None
        self.service_browser: Optional[ServiceBrowser] = None
        self.peers_lock: asyncio.Lock = asyncio.Lock()
        self.event_loop: Optional[asyncio.AbstractEventLoop] = None
        self.server: Optional[asyncio.Server] = None

        # Gossip protocol state
        self.seen_messages: deque = deque(maxlen=self.SEEN_MESSAGES_MAX_SIZE)

    def _load_or_create_identity(self) -> None:
        """Load or create Ed25519 cryptographic identity."""
        key_file = Path("node.key")

        if key_file.exists():
            with open(key_file, "r") as f:
                key_data = json.load(f)
            key_bytes = base64.b64decode(key_data["signing_key"])
            self.signing_key = nacl.signing.SigningKey(key_bytes)
        else:
            self.signing_key = nacl.signing.SigningKey.generate()
            key_data = {
                "signing_key": base64.b64encode(bytes(self.signing_key)).decode(),
                "created": datetime.now().isoformat(),
            }
            with open(key_file, "w") as f:
                json.dump(key_data, f, indent=2)

        self.node_id = self.signing_key.verify_key
        self.node_id_b64 = (
            base64.urlsafe_b64encode(bytes(self.node_id)).decode().rstrip("=")
        )

    def _find_available_port(self) -> int:
        """Find an available TCP port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("0.0.0.0", 0))
            s.listen(1)
            _, port = s.getsockname()
        return port

    def _get_local_ip(self) -> str:
        """Determine the local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    async def initialize(self) -> None:
        """Initialize the node: identity, port, Zeroconf, and TCP server."""
        self.event_loop = asyncio.get_event_loop()
        self._load_or_create_identity()
        self.tcp_port = self._find_available_port()
        self.local_ip = self._get_local_ip()

        await self._start_tcp_server()
        await self._setup_zeroconf()

    async def _start_tcp_server(self) -> None:
        """Start the TCP server."""
        self.server = await asyncio.start_server(
            self.handle_connection, self.local_ip, self.tcp_port
        )

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """
        Handle incoming TCP connection.

        Implements gossip logic:
        1. Check for duplicate messages
        2. Forward non-duplicate messages if ttl > 0
        3. Display to UI if it's a CHAT message
        """
        addr = writer.get_extra_info("peername")
        try:
            data = await reader.readuntil(self.MESSAGE_TERMINATOR)

            if data:
                message_json = data.decode(self.MESSAGE_ENCODING).strip()
                try:
                    message = json.loads(message_json)
                    msg_type = message.get("type")

                    if msg_type == "HELLO":
                        # HELLO message: just send ACK
                        writer.write(b"ACK\n")
                        await writer.drain()

                    elif msg_type == "CHAT":
                        # CHAT message: implement gossip logic
                        msg_id = message.get("msg_id")

                        # Check if we've seen this message before (duplicate detection)
                        if msg_id in self.seen_messages:
                            logger.debug(f"Ignoring duplicate message: {msg_id}")
                            writer.write(b"ACK\n")
                            await writer.drain()
                            return

                        # New message: add to seen cache
                        self.seen_messages.append(msg_id)

                        # Extract sender information
                        from_peer = message.get("from", "Unknown")
                        content = message.get("content", "")

                        # Display to UI (preserving original sender)
                        self.app.on_message_received(from_peer, content)

                        # Forward message if ttl > 0 (gossip logic)
                        ttl = message.get("ttl", 0)
                        if ttl > 0:
                            # Get the peer that sent us this message
                            # (extracted from addr, but for simplicity use None)
                            await self.forward_message(message, addr)

                        # Send ACK
                        writer.write(b"ACK\n")
                        await writer.drain()

                except json.JSONDecodeError:
                    writer.write(b"ERROR\n")
                    await writer.drain()

        except asyncio.LimitOverrunError:
            logger.warning(f"Message from {addr} exceeds size limit")
            writer.close()
            await writer.wait_closed()
        except Exception as e:
            logger.warning(f"Error handling connection from {addr}: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def forward_message(
        self, message: dict, received_from_addr: tuple
    ) -> None:
        """
        Forward a message to all peers (except the sender).

        Implements gossip forwarding:
        1. Decrement ttl
        2. Send to all peers (excluding sender)
        3. Run asynchronously to avoid blocking

        Args:
            message: The message to forward (will be modified with new ttl)
            received_from_addr: Tuple (ip, port) of the sender
        """
        # Create a copy and decrement ttl
        forwarded_message = message.copy()
        forwarded_message["ttl"] = forwarded_message.get("ttl", 1) - 1

        # If ttl becomes 0, don't forward
        if forwarded_message["ttl"] <= 0:
            logger.debug(f"Message {message.get('msg_id')} ttl exhausted, not forwarding")
            return

        # Get all peers
        async with self.peers_lock:
            peer_list = list(self.peers.items())

        # Forward to each peer asynchronously
        for peer_id, peer_info in peer_list:
            # Create a task for each peer to avoid blocking
            asyncio.create_task(
                self._forward_to_peer(peer_id, peer_info, forwarded_message)
            )

    async def _forward_to_peer(
        self, peer_id: str, peer_info: Dict[str, str], message: dict
    ) -> None:
        """
        Send a forwarded message to a specific peer.

        Args:
            peer_id: ID of the target peer
            peer_info: Dictionary with 'ip' and 'port'
            message: The message to send
        """
        peer_ip = peer_info["ip"]
        peer_port = int(peer_info["port"])

        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)

            message_json = json.dumps(message)
            message_bytes = (message_json + "\n").encode(self.MESSAGE_ENCODING)

            writer.write(message_bytes)
            await writer.drain()

            # Wait for ACK
            ack_data = await asyncio.wait_for(
                reader.readuntil(self.MESSAGE_TERMINATOR), timeout=2.0
            )

            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError):
            logger.debug(f"Could not forward to {peer_id} ({peer_ip}:{peer_port})")
        except Exception as e:
            logger.debug(f"Error forwarding to {peer_id}: {e}")

    async def _setup_zeroconf(self) -> None:
        """Initialize Zeroconf service publishing and discovery."""
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)

        properties = {
            "id": self.node_id_b64,
            "version": "0.2",  # Gossip protocol version
            "p": str(self.tcp_port),
        }

        node_id_short = self.node_id_b64[:8]
        service_name = f"TAZCOM Node {node_id_short}._tazcom._tcp.local."

        info = ServiceInfo(
            "_tazcom._tcp.local.",
            service_name,
            addresses=[socket.inet_aton(self.local_ip)],
            port=self.tcp_port,
            properties=properties,
            server=f"tazcom-{node_id_short}.local.",
        )

        await self.aiozc.async_register_service(info)

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
        """Handle service state changes."""
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
        """Handle peer discovery."""
        try:
            info = zeroconf.get_service_info(service_type, name)
            if info is None:
                return

            properties = info.properties or {}
            peer_id_bytes = properties.get(b"id")
            if not peer_id_bytes:
                return
            peer_id = (
                peer_id_bytes.decode()
                if isinstance(peer_id_bytes, bytes)
                else peer_id_bytes
            )

            if peer_id == self.node_id_b64:
                return

            addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
            peer_ip = addresses[0] if addresses else "unknown"
            peer_port = info.port

            async with self.peers_lock:
                self.peers[peer_id] = {
                    "ip": peer_ip,
                    "port": str(peer_port),
                    "name": name,
                }
                self.service_name_to_id[name] = peer_id

            self.app.on_peer_update()

            await self.send_hello(peer_id)

        except Exception as e:
            logger.warning(f"Error processing service addition: {e}")

    async def _on_service_removed(self, name: str) -> None:
        """Handle peer removal."""
        async with self.peers_lock:
            peer_id = self.service_name_to_id.pop(name, None)
            if peer_id and peer_id in self.peers:
                del self.peers[peer_id]

        self.app.on_peer_update()

    async def send_hello(self, peer_id: str) -> None:
        """Send a HELLO greeting to a peer."""
        async with self.peers_lock:
            peer_info = self.peers.get(peer_id)
            if not peer_info:
                return
            peer_ip = peer_info["ip"]
            peer_port = int(peer_info["port"])

        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)
            hello_message = {
                "type": "HELLO",
                "from": self.node_id_b64,
            }
            message_json = json.dumps(hello_message)
            message_bytes = (message_json + "\n").encode(self.MESSAGE_ENCODING)

            writer.write(message_bytes)
            await writer.drain()

            ack_data = await reader.readuntil(self.MESSAGE_TERMINATOR)
            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError):
            pass
        except Exception as e:
            logger.debug(f"Error sending HELLO to {peer_id}: {e}")

    async def broadcast_message(self, content: str) -> None:
        """
        Broadcast a message to all peers with gossip metadata.

        Creates a new message with:
        - Unique msg_id (hash of content + timestamp)
        - Initial ttl (for multi-hop delivery)
        - Adds to seen_messages to prevent loops

        Args:
            content: The message content from the user
        """
        if not content.strip():
            return

        # Generate unique msg_id based on content and timestamp
        timestamp = datetime.now().isoformat()
        msg_id_input = f"{content}:{timestamp}:{self.node_id_b64}"
        msg_id = hashlib.sha256(msg_id_input.encode()).hexdigest()[:16]

        # Add to seen messages to prevent loops
        self.seen_messages.append(msg_id)

        # Create gossip message
        chat_message = {
            "type": "CHAT",
            "msg_id": msg_id,
            "from": self.node_id_b64,
            "timestamp": timestamp,
            "content": content,
            "ttl": self.INITIAL_TTL,
        }

        # Broadcast to all direct peers
        async with self.peers_lock:
            peer_list = list(self.peers.items())

        for peer_id, peer_info in peer_list:
            asyncio.create_task(
                self._send_chat_message(peer_id, peer_info, chat_message)
            )

    async def _send_chat_message(
        self, peer_id: str, peer_info: Dict[str, str], message: dict
    ) -> None:
        """Send a CHAT message to a specific peer."""
        peer_ip = peer_info["ip"]
        peer_port = int(peer_info["port"])

        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)

            message_json = json.dumps(message)
            message_bytes = (message_json + "\n").encode(self.MESSAGE_ENCODING)

            writer.write(message_bytes)
            await writer.drain()

            ack_data = await reader.readuntil(self.MESSAGE_TERMINATOR)
            writer.close()
            await writer.wait_closed()

        except (ConnectionRefusedError, asyncio.TimeoutError):
            pass
        except Exception as e:
            logger.debug(f"Error sending CHAT to {peer_id}: {e}")

    async def shutdown(self) -> None:
        """Gracefully shut down the node."""
        if self.server:
            self.server.close()
            await self.server.wait_closed()

        if self.aiozc:
            await self.aiozc.async_close()


class PeerListWidget(Static):
    """Display list of discovered peers."""

    def __init__(self) -> None:
        super().__init__()
        self.peers: Dict[str, str] = {}

    def update_peers(self, peers: Dict[str, Dict[str, str]]) -> None:
        """Update the peer list."""
        self.peers = {pid: pid[:8] for pid in peers.keys()}
        self.refresh()

    def render(self) -> str:
        """Render the peer list."""
        if not self.peers:
            return "[dim]No peers discovered[/dim]"

        peer_lines = [f"[green]●[/green] {name}" for name in self.peers.values()]
        return "[bold]Peers:[/bold]\n" + "\n".join(peer_lines)


class MessageHistoryWidget(RichLog):
    """Display chat message history."""

    def __init__(self) -> None:
        super().__init__()
        self.message_count = 0

    def add_local_message(self, content: str) -> None:
        """Add a message sent by this node."""
        self.write(f"[bold cyan]You:[/bold cyan] {content}")
        self.message_count += 1

    def add_remote_message(self, from_peer: str, content: str) -> None:
        """Add a message received from a peer."""
        peer_short = from_peer[:8]
        self.write(f"[bold green]{peer_short}:[/bold green] {content}")
        self.message_count += 1

    def add_system_message(self, content: str) -> None:
        """Add a system message."""
        self.write(f"[dim]{content}[/dim]")


class TAZCOMChatAppGossip(App):
    """Main Textual chat application with Gossip Protocol."""

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 1;
        background: $surface;
        color: $text;
    }

    #container {
        height: 1fr;
    }

    #chat_area {
        width: 1fr;
        height: 1fr;
    }

    #peer_list {
        width: 20;
        height: 1fr;
        border: solid $accent;
    }

    #message_history {
        width: 1fr;
        height: 1fr;
    }

    #input_area {
        height: 3;
        border: solid $accent;
    }

    Input {
        width: 1fr;
    }
    """

    def __init__(self):
        super().__init__()
        self.node: Optional[TAZCOMNodeGossip] = None
        self.peer_list: Optional[PeerListWidget] = None
        self.message_history: Optional[MessageHistoryWidget] = None
        self.input_widget: Optional[Input] = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header(show_clock=True)

        with Container(id="container"):
            with Horizontal(id="chat_area"):
                self.peer_list = PeerListWidget(id="peer_list")
                yield self.peer_list

                self.message_history = MessageHistoryWidget(id="message_history")
                yield self.message_history

            self.input_widget = Input(
                placeholder="Type message and press Enter (gossip protocol enabled)...",
                id="input_area",
            )
            yield self.input_widget

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the backend and start monitoring."""
        self.node = TAZCOMNodeGossip(self)
        await self.node.initialize()

        self.title = f"TAZCOM Mesh Chat (Gossip) - {self.node.node_id_b64[:8]}"

        self.message_history.add_system_message(
            f"[bold]Node initialized:[/bold] {self.node.node_id_b64[:8]} @ "
            f"{self.node.local_ip}:{self.node.tcp_port} [italic](Gossip Protocol v0.2)[/italic]"
        )

        self.input_widget.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        content = event.value.strip()
        if not content:
            return

        if not self.node:
            return

        self.input_widget.value = ""

        self.message_history.add_local_message(content)

        await self.node.broadcast_message(content)

    def on_peer_update(self) -> None:
        """Called by backend when peer list changes."""
        if self.node and self.peer_list:
            self.peer_list.update_peers(self.node.peers)

    def on_message_received(self, from_peer: str, content: str) -> None:
        """Called by backend when a message is received."""
        if self.message_history:
            self.message_history.add_remote_message(from_peer, content)

    async def action_quit(self) -> None:
        """Gracefully shut down."""
        if self.node:
            await self.node.shutdown()
        self.exit()


async def main() -> None:
    """Main entry point."""
    app = TAZCOMChatAppGossip()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
