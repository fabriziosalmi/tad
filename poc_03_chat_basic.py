"""
poc-03_chat_basic.py - TAZCOM PoC Milestone 3: Interactive TUI Chat

This is a fully integrated peer-to-peer chat application that combines:
1. TAZCOMNode backend (from poc-02) for discovery and TCP communication
2. Textual TUI framework for interactive user interface
3. Real-time message history and peer list

Each node:
- Discovers peers on the local network via mDNS
- Maintains a list of active peers
- Allows users to type messages in a text input
- Broadcasts messages to all discovered peers
- Receives and displays messages from peers in real-time
- Shows peer list with online/offline status

To run:
    python poc-03_chat_basic.py

Then open multiple terminals and run the same command.
The UI will display discovered peers and allow real-time chat.

Controls:
    Type message + Enter: Send to all peers
    Ctrl+C: Quit gracefully
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
from textual.app import ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, RichLog, Static
from textual.app import App
from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceStateChange, Zeroconf
from zeroconf.asyncio import AsyncZeroconf

# Configure logging (minimal output, mostly for backend errors)
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)-5s] %(message)s",
)


class TAZCOMNode:
    """
    TAZCOM network node backend for chat application.

    Refactored to act as an event-driven engine that emits signals to the UI
    rather than managing its own event loop.

    Events emitted:
    - peer_added(peer_id, peer_ip, peer_port)
    - peer_removed(peer_id)
    - message_received(from_peer_id, message_content)
    """

    # Message protocol constants
    MESSAGE_ENCODING = "utf-8"
    MESSAGE_TERMINATOR = b"\n"
    MESSAGE_SIZE_LIMIT = 1024

    def __init__(self, app: "TAZCOMChatApp") -> None:
        """
        Initialize a TAZCOM node.

        Args:
            app: Reference to the Textual app instance for callbacks.
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
        """Handle incoming TCP connection."""
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
                        # CHAT message: emit to UI and send ACK
                        from_peer = message.get("from", "Unknown")
                        content = message.get("content", "")
                        self.app.on_message_received(from_peer, content)
                        writer.write(b"ACK\n")
                        await writer.drain()

                except json.JSONDecodeError:
                    # Invalid JSON, send error ACK
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

    async def _setup_zeroconf(self) -> None:
        """Initialize Zeroconf service publishing and discovery."""
        self.aiozc = AsyncZeroconf(ip_version=IPVersion.V4Only)

        properties = {
            "id": self.node_id_b64,
            "version": "0.1",
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

            # Notify UI of peer addition
            self.app.on_peer_update()

            # Send HELLO to new peer
            await self.send_hello(peer_id)

        except Exception as e:
            logger.warning(f"Error processing service addition: {e}")

    async def _on_service_removed(self, name: str) -> None:
        """Handle peer removal."""
        async with self.peers_lock:
            peer_id = self.service_name_to_id.pop(name, None)
            if peer_id and peer_id in self.peers:
                del self.peers[peer_id]

        # Notify UI of peer removal
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
            pass  # Silently handle connection issues
        except Exception as e:
            logger.debug(f"Error sending HELLO to {peer_id}: {e}")

    async def broadcast_message(self, content: str) -> None:
        """
        Broadcast a CHAT message to all discovered peers.

        Args:
            content: The message content to broadcast.
        """
        async with self.peers_lock:
            peer_list = list(self.peers.items())

        for peer_id, peer_info in peer_list:
            asyncio.create_task(
                self._send_chat_message(peer_id, peer_info, content)
            )

    async def _send_chat_message(
        self, peer_id: str, peer_info: Dict[str, str], content: str
    ) -> None:
        """Send a CHAT message to a specific peer."""
        peer_ip = peer_info["ip"]
        peer_port = int(peer_info["port"])

        try:
            reader, writer = await asyncio.open_connection(peer_ip, peer_port)

            chat_message = {
                "type": "CHAT",
                "from": self.node_id_b64,
                "timestamp": datetime.now().isoformat(),
                "content": content,
            }
            message_json = json.dumps(chat_message)
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


class HeaderWidget(Static):
    """Header showing node ID and status."""

    def __init__(self, node_id: str, node_ip: str, node_port: int) -> None:
        super().__init__()
        self.node_id = node_id[:8]
        self.node_ip = node_ip
        self.node_port = node_port

    def render(self) -> str:
        """Render the header."""
        return f"[bold cyan]TAZCOM Chat[/bold cyan] | Node: [yellow]{self.node_id}[/yellow] | {self.node_ip}:{self.node_port}"


class PeerListWidget(Static):
    """Display list of discovered peers."""

    def __init__(self) -> None:
        super().__init__()
        self.peers: Dict[str, str] = {}  # peer_id -> display_name

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


class TAZCOMChatApp(App):
    """Main Textual chat application."""

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
        self.node: Optional[TAZCOMNode] = None
        self.header_widget: Optional[HeaderWidget] = None
        self.peer_list: Optional[PeerListWidget] = None
        self.message_history: Optional[MessageHistoryWidget] = None
        self.input_widget: Optional[Input] = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        # Header
        yield Header(show_clock=True)

        # Main container
        with Container(id="container"):
            # Chat area (peer list + message history)
            with Horizontal(id="chat_area"):
                self.peer_list = PeerListWidget(id="peer_list")
                yield self.peer_list

                self.message_history = MessageHistoryWidget(id="message_history")
                yield self.message_history

            # Input area
            self.input_widget = Input(
                placeholder="Type message and press Enter to broadcast...",
                id="input_area",
            )
            yield self.input_widget

        yield Footer()

    async def on_mount(self) -> None:
        """Initialize the backend and start monitoring."""
        # Create and initialize the node
        self.node = TAZCOMNode(self)
        await self.node.initialize()

        # Update header with node info
        self.title = f"TAZCOM Chat - {self.node.node_id_b64[:8]}"

        # Show initial message
        self.message_history.add_system_message(
            f"[bold]Node initialized:[/bold] {self.node.node_id_b64[:8]} @ "
            f"{self.node.local_ip}:{self.node.tcp_port}"
        )

        # Focus on input
        self.input_widget.focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle message input submission."""
        content = event.value.strip()
        if not content:
            return

        if not self.node:
            return

        # Clear input
        self.input_widget.value = ""

        # Display local message
        self.message_history.add_local_message(content)

        # Broadcast to peers
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
    app = TAZCOMChatApp()
    await app.run_async()


if __name__ == "__main__":
    asyncio.run(main())
