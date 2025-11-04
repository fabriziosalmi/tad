"""
TAD Advanced TUI Application (Milestone 5)

Modern, multi-channel interface with:
- Dynamic channel management (/join, /leave, /switch)
- Real-time peer display
- Message history with persistence
- Command system for power users
- Responsive layout with sidebar and panels
"""

import asyncio
import logging
from typing import Optional

from textual.app import ComposeResult, on
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Label
from textual.screen import Screen

from .node import TADNode
from .ui import ChannelList, CommandInput, MessageView, PeerList, UIState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)-20s] [%(levelname)-5s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class TADTUIApp(Screen):
    """
    Main TAD Advanced TUI Application.

    Provides a modern, multi-channel interface for the TAD network with:
    - Channel list sidebar
    - Message view center
    - Peer list sidebar
    - Command input at bottom
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("?", "help", "Help"),
        ("n", "new_channel", "New Channel"),
        ("d", "delete_channel", "Delete Channel"),
        ("tab", "next_channel", "Next Channel"),
        ("shift+tab", "prev_channel", "Prev Channel"),
    ]

    DEFAULT_CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-rows: auto 1fr auto;
        grid-columns: 1fr 3fr 1fr;
    }

    #header {
        column-span: 3;
        background: $boost;
        color: $text;
        border: solid $accent;
    }

    #channel_panel {
        row-span: 2;
        column: 0;
        border: solid $primary;
    }

    #message_panel {
        row-span: 2;
        column: 1;
        border: solid $primary;
    }

    #peer_panel {
        row-span: 2;
        column: 2;
        border: solid $primary;
    }

    #input_panel {
        column-span: 3;
        border: solid $primary;
    }

    #footer {
        column-span: 3;
        background: $boost;
        color: $text;
    }
    """

    def __init__(self, node: TADNode, **kwargs):
        """
        Initialize the TUI application.

        Args:
            node: TADNode instance for network communication
        """
        super().__init__(**kwargs)
        self.node = node
        self.ui_state = UIState()

        # UI components
        self.channel_list: Optional[ChannelList] = None
        self.message_view: Optional[MessageView] = None
        self.peer_list: Optional[PeerList] = None
        self.command_input: Optional[CommandInput] = None

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header(id="header")

        with Horizontal():
            yield ChannelList(id="channel_panel")
            yield MessageView(id="message_panel")
            yield PeerList(id="peer_panel")

        yield CommandInput(id="input_panel")
        yield Footer(id="footer")

    def on_mount(self) -> None:
        """Initialize the UI when mounted."""
        # Get widget references
        self.channel_list = self.query_one("#channel_panel", ChannelList)
        self.message_view = self.query_one("#message_panel", MessageView)
        self.peer_list = self.query_one("#peer_panel", PeerList)
        self.command_input = self.query_one("#input_panel", CommandInput)

        # Set up callbacks
        self.command_input.on_message = self._handle_message
        self.command_input.on_command = self._handle_command

        # Initialize channels from node
        logger.info("Initializing TUI...")
        for channel in self.ui_state.subscribed_channels:
            self.channel_list.add_channel(channel)

        # Set active channel
        self.channel_list.set_active_channel(self.ui_state.active_channel)

        # Load message history
        self._load_channel_history(self.ui_state.active_channel)

        logger.info("TUI initialized successfully")

    async def _load_channel_history(self, channel_id: str) -> None:
        """Load and display message history for a channel."""
        self.message_view.clear_messages()

        try:
            history = await self.node.load_channel_history(channel_id, last_n=50)

            if history:
                self.message_view.add_system_message(
                    f"Loaded {len(history)} messages from {channel_id}"
                )

                for msg in history:
                    payload = msg.get("payload", {})
                    sender = msg.get("sender_id", "unknown")[:8]
                    timestamp = payload.get("timestamp", "")
                    content = payload.get("content", "")
                    channel = payload.get("channel_id", channel_id)

                    self.message_view.add_message(
                        content=content,
                        sender=sender,
                        channel=channel,
                        timestamp=timestamp[:16] if timestamp else "",
                    )
            else:
                self.message_view.add_system_message(
                    f"No messages yet in {channel_id}"
                )

        except Exception as e:
            self.message_view.add_system_message(f"Error loading history: {e}")
            logger.error(f"Error loading channel history: {e}")

    def _handle_message(self, content: str) -> None:
        """Handle a regular message from the user."""
        if not content.strip():
            return

        # Send message via node
        try:
            msg_id = self.app.call_from_thread(
                self.node.broadcast_message,
                content,
                self.ui_state.active_channel,
            )

            logger.info(f"Message sent: {msg_id}")

            # Display message immediately
            self.message_view.add_message(
                content=content,
                sender=self.node.username,
                channel=self.ui_state.active_channel,
            )

        except Exception as e:
            self.message_view.add_system_message(f"Error sending message: {e}")
            logger.error(f"Error sending message: {e}")

    def _handle_command(self, command: str, args: list) -> None:
        """Handle a command from the user."""
        logger.info(f"Command: {command} {' '.join(args)}")

        if command == "join":
            self._cmd_join(args)
        elif command == "leave":
            self._cmd_leave(args)
        elif command in ("switch", "s"):
            self._cmd_switch(args)
        elif command == "channels":
            self._cmd_channels(args)
        elif command == "peers":
            self._cmd_peers(args)
        elif command == "help":
            self._cmd_help(args)
        else:
            self.message_view.add_command_output(f"Unknown command: /{command}")

    def _cmd_join(self, args: list) -> None:
        """Handle /join command."""
        if not args:
            self.message_view.add_command_output("Usage: /join <#channel>")
            return

        channel_id = args[0]
        if not channel_id.startswith("#"):
            channel_id = f"#{channel_id}"

        # Join via node
        self.node.join_channel(channel_id)
        self.ui_state.add_channel(channel_id)

        # Update UI
        self.channel_list.add_channel(channel_id)
        self.message_view.add_system_message(f"Joined {channel_id}")

        logger.info(f"Joined channel: {channel_id}")

    def _cmd_leave(self, args: list) -> None:
        """Handle /leave command."""
        if not args:
            self.message_view.add_command_output("Usage: /leave <#channel>")
            return

        channel_id = args[0]
        if not channel_id.startswith("#"):
            channel_id = f"#{channel_id}"

        # Can't leave the default channel
        if channel_id == "#general":
            self.message_view.add_system_message("Cannot leave #general")
            return

        # Leave via node
        self.node.leave_channel(channel_id)
        self.ui_state.remove_channel(channel_id)

        # Update UI
        self.channel_list.remove_channel(channel_id)

        # Switch to #general if current
        if self.ui_state.active_channel == channel_id:
            self._cmd_switch(["#general"])

        self.message_view.add_system_message(f"Left {channel_id}")
        logger.info(f"Left channel: {channel_id}")

    def _cmd_switch(self, args: list) -> None:
        """Handle /switch and /s commands."""
        if not args:
            self.message_view.add_command_output("Usage: /switch <#channel>")
            return

        channel_id = args[0]
        if not channel_id.startswith("#"):
            channel_id = f"#{channel_id}"

        if not self.ui_state.switch_channel(channel_id):
            self.message_view.add_command_output(f"Not subscribed to {channel_id}")
            return

        # Update UI
        self.channel_list.set_active_channel(channel_id)
        self.message_view.clear_messages()

        # Load history asynchronously
        self.app.call_later(self._load_channel_history, channel_id)

        self.message_view.add_system_message(f"Switched to {channel_id}")
        logger.info(f"Switched to channel: {channel_id}")

    def _cmd_channels(self, args: list) -> None:
        """Handle /channels command."""
        channels = list(self.ui_state.subscribed_channels)
        channels.sort()

        output = "Subscribed channels:\n"
        for ch in channels:
            marker = "▶" if ch == self.ui_state.active_channel else " "
            output += f"  {marker} {ch}\n"

        self.message_view.add_command_output(output)

    def _cmd_peers(self, args: list) -> None:
        """Handle /peers command."""
        count = self.peer_list.get_peer_count()
        output = f"Connected peers: {count}"
        self.message_view.add_command_output(output)

    def _cmd_help(self, args: list) -> None:
        """Handle /help command."""
        help_text = """Available Commands:
  /join <#channel>      - Join a channel
  /leave <#channel>     - Leave a channel
  /switch <#channel>    - Switch to a channel
  /s <#channel>         - Shortcut for /switch
  /channels             - List all subscribed channels
  /peers                - Show connected peers
  /help                 - Show this help message

Keyboard Shortcuts:
  Tab          - Next channel
  Shift+Tab    - Previous channel
  Ctrl+C       - Quit
  ?            - Help

Multi-channel messaging: Type normally to send a message to the active channel."""

        self.message_view.add_command_output(help_text)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

    def action_help(self) -> None:
        """Show help."""
        self._cmd_help([])

    def action_new_channel(self) -> None:
        """Prompt for new channel (future feature)."""
        self.message_view.add_command_output("Use /join <#channel> to join a channel")

    def action_delete_channel(self) -> None:
        """Prompt for channel to delete (future feature)."""
        self.message_view.add_command_output(
            "Use /leave <#channel> to leave a channel"
        )

    def action_next_channel(self) -> None:
        """Switch to next channel."""
        channels = sorted(self.ui_state.subscribed_channels)
        if not channels:
            return

        current_idx = channels.index(self.ui_state.active_channel)
        next_idx = (current_idx + 1) % len(channels)
        self._cmd_switch([channels[next_idx]])

    def action_prev_channel(self) -> None:
        """Switch to previous channel."""
        channels = sorted(self.ui_state.subscribed_channels)
        if not channels:
            return

        current_idx = channels.index(self.ui_state.active_channel)
        prev_idx = (current_idx - 1) % len(channels)
        self._cmd_switch([channels[prev_idx]])


async def main() -> None:
    """Main entry point for the TAD TUI application."""
    # Create TAD node
    node = TADNode(username="TUI_User")

    try:
        await node.start()
        logger.info("TAD node started")

        # Run Textual app
        app = TADTUIApp(node)
        await app.run_async()

    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        await node.stop()
        logger.info("TAD node stopped")


if __name__ == "__main__":
    asyncio.run(main())
