"""
TAD Advanced TUI Widgets (Milestone 5)

Custom Textual widgets for the advanced TAD interface:
- ChannelList: Channel management and selection
- PeerList: Peer display for active channel
- MessageView: Message history and display
- CommandInput: Command parsing and input handling
"""

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Set

from textual.containers import Container, Vertical, Horizontal
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    RichLog,
    Static,
    Footer,
    Header,
)
from textual.reactive import reactive
from rich.text import Text
from rich.console import RenderableType


class ChannelItem(ListItem):
    """Represents a single channel in the channel list."""

    def __init__(
        self,
        channel_id: str,
        channel_type: str = "public",
        unread_count: int = 0,
        is_active: bool = False,
        **kwargs,
    ):
        """
        Initialize a channel list item.

        Args:
            channel_id: Channel identifier (e.g., "#general")
            channel_type: Type of the channel ('public' or 'private')
            unread_count: Number of unread messages
            is_active: Whether this is the currently selected channel
        """
        self.channel_id = channel_id
        self.channel_type = channel_type
        self.unread_count = unread_count
        self.is_active = is_active

        # Format the display label with optional badge and lock icon
        label_text = self._format_label()

        super().__init__(Label(label_text), **kwargs)

    def _format_label(self) -> str:
        """Format the display label with icon and unread count."""
        prefix = "🔒 " if self.channel_type == "private" else ""
        suffix = f" ({self.unread_count})" if self.unread_count > 0 else ""
        return f"{prefix}{self.channel_id}{suffix}"

    def update_unread(self, count: int) -> None:
        """Update the unread message count."""
        self.unread_count = count
        label_text = self._format_label()

        # Update the label widget
        if self.children:
            label = self.children[0]
            if isinstance(label, Label):
                label.update(label_text)


class ChannelList(Static):
    """
    Displays the list of subscribed channels.

    Features:
    - Show all subscribed channels
    - Highlight currently active channel
    - Show unread message badges
    - Allow channel selection
    """

    DEFAULT_CSS = """
    ChannelList {
        width: 20;
        border: solid $accent;
        height: 1fr;
    }

    ChannelList ListView {
        height: 1fr;
    }
    """

    def __init__(self, on_channel_selected: Optional[Callable] = None, **kwargs):
        """
        Initialize ChannelList widget.

        Args:
            on_channel_selected: Callback when user selects a channel
        """
        super().__init__(**kwargs)
        self.on_channel_selected = on_channel_selected
        self.channel_items: Dict[str, ChannelItem] = {}
        self.active_channel: Optional[str] = None

    def compose(self):
        """Compose the widget."""
        yield ListView(id="channel_list")

    def add_channel(self, channel_id: str, channel_type: str = "public") -> None:
        """Add a channel to the list."""
        if channel_id not in self.channel_items:
            item = ChannelItem(
                channel_id,
                channel_type=channel_type,
                is_active=(channel_id == self.active_channel),
            )
            self.channel_items[channel_id] = item

            list_view = self.query_one("#channel_list", ListView)
            list_view.append(item)

    def remove_channel(self, channel_id: str) -> None:
        """Remove a channel from the list."""
        if channel_id in self.channel_items:
            item = self.channel_items[channel_id]
            item.remove()
            del self.channel_items[channel_id]

    def set_active_channel(self, channel_id: str) -> None:
        """Set the currently active channel."""
        # Reset previous active
        if self.active_channel and self.active_channel in self.channel_items:
            prev_item = self.channel_items[self.active_channel]
            prev_item.is_active = False
            # Update styling if possible

        # Set new active
        if channel_id in self.channel_items:
            self.active_channel = channel_id
            item = self.channel_items[channel_id]
            item.is_active = True

            # Scroll to visible
            list_view = self.query_one("#channel_list", ListView)
            list_view.focus()

    def update_unread_badge(self, channel_id: str, count: int) -> None:
        """Update the unread message badge for a channel."""
        if channel_id in self.channel_items:
            self.channel_items[channel_id].update_unread(count)

    def get_channels(self) -> List[str]:
        """Get list of all channels."""
        return list(self.channel_items.keys())


class PeerList(Static):
    """
    Displays the list of active peers in the selected channel.

    Features:
    - Show connected peers
    - Show peer status
    - Update in real-time
    """

    DEFAULT_CSS = """
    PeerList {
        width: 20;
        border: solid $accent;
        height: 1fr;
    }

    PeerList ListView {
        height: 1fr;
    }
    """

    def __init__(self, **kwargs):
        """Initialize PeerList widget."""
        super().__init__(**kwargs)
        self.peer_items: Dict[str, ListItem] = {}

    def compose(self):
        """Compose the widget."""
        yield ListView(id="peer_list")

    def add_peer(self, peer_id: str) -> None:
        """Add a peer to the list."""
        if peer_id not in self.peer_items:
            # Show only first 8 chars of peer ID
            peer_label = f"👤 {peer_id[:8]}..."
            item = ListItem(Label(peer_label))
            self.peer_items[peer_id] = item

            list_view = self.query_one("#peer_list", ListView)
            list_view.append(item)

    def remove_peer(self, peer_id: str) -> None:
        """Remove a peer from the list."""
        if peer_id in self.peer_items:
            item = self.peer_items[peer_id]
            item.remove()
            del self.peer_items[peer_id]

    def clear_peers(self) -> None:
        """Clear all peers from the list."""
        list_view = self.query_one("#peer_list", ListView)
        list_view.clear()
        self.peer_items.clear()

    def get_peer_count(self) -> int:
        """Get number of connected peers."""
        return len(self.peer_items)


class MessageView(Static):
    """
    Displays message history for the selected channel.

    Features:
    - Show message history with formatting
    - Display sender, timestamp, content
    - Auto-scroll to latest message
    - Support for different message types
    """

    DEFAULT_CSS = """
    MessageView {
        height: 1fr;
        border: solid $accent;
        background: $surface;
    }

    MessageView RichLog {
        height: 1fr;
        width: 1fr;
    }
    """

    def __init__(self, **kwargs):
        """Initialize MessageView widget."""
        super().__init__(**kwargs)
        self.current_channel: Optional[str] = None

    def compose(self):
        """Compose the widget."""
        yield RichLog(id="message_log", markup=True)

    def clear_messages(self) -> None:
        """Clear all messages from the view."""
        log = self.query_one("#message_log", RichLog)
        log.clear()

    def add_message(
        self,
        content: str,
        sender: str = "System",
        channel: str = "#general",
        timestamp: str = "",
    ) -> None:
        """
        Add a message to the view.

        Args:
            content: Message content
            sender: Sender identifier (nickname or short ID)
            channel: Channel the message is from
            timestamp: Message timestamp
        """
        log = self.query_one("#message_log", RichLog)

        # Format message with colors and structure
        formatted = Text()
        formatted.append(f"[{timestamp}] " if timestamp else "")
        formatted.append(f"[{channel}] ", style="cyan")
        formatted.append(f"<{sender}> ", style="yellow bold")
        formatted.append(content, style="white")

        log.write(formatted)

    def add_system_message(self, message: str) -> None:
        """Add a system message (e.g., user joined, left)."""
        log = self.query_one("#message_log", RichLog)
        formatted = Text(f"→ {message}", style="cyan italic")
        log.write(formatted)

    def add_command_output(self, output: str) -> None:
        """Add command output to the view."""
        log = self.query_one("#message_log", RichLog)
        formatted = Text(output, style="green")
        log.write(formatted)


class CommandInput(Static):
    """
    Input widget with command parsing.

    Features:
    - Parse commands starting with /
    - Send messages starting with other characters
    - Command suggestions and help
    """

    DEFAULT_CSS = """
    CommandInput {
        height: 3;
        border: solid $accent;
    }

    CommandInput Input {
        width: 1fr;
    }
    """

    def __init__(
        self,
        on_message: Optional[Callable[[str], None]] = None,
        on_command: Optional[Callable[[str, List[str]], None]] = None,
        **kwargs,
    ):
        """
        Initialize CommandInput widget.

        Args:
            on_message: Callback when user sends a message
            on_command: Callback when user executes a command
        """
        super().__init__(**kwargs)
        self.on_message = on_message
        self.on_command = on_command
        self.history: List[str] = []
        self.history_index = -1

    def compose(self):
        """Compose the widget."""
        yield Input(
            id="command_input",
            placeholder="Type message or /help for commands",
        )

    def on_mount(self) -> None:
        """Set up event handlers when widget is mounted."""
        input_widget = self.query_one("#command_input", Input)
        input_widget.focus()

    def parse_input(self, text: str) -> None:
        """
        Parse input and determine if it's a command or message.

        Args:
            text: Raw input text
        """
        text = text.strip()

        if not text:
            return

        # Add to history
        self.history.append(text)
        self.history_index = -1

        if text.startswith("/"):
            # Command
            self._handle_command(text)
        else:
            # Message
            if self.on_message:
                self.on_message(text)

        # Clear input
        input_widget = self.query_one("#command_input", Input)
        input_widget.value = ""

    def _handle_command(self, text: str) -> None:
        """Handle a command."""
        parts = text.split()
        if not parts:
            return

        command = parts[0][1:].lower()  # Remove leading /
        args = parts[1:]

        if self.on_command:
            self.on_command(command, args)


@dataclass
class UIState:
    """Manages UI state for the TUI application."""

    active_channel: str = "#general"
    subscribed_channels: Set[str] = field(default_factory=lambda: {"#general"})
    unread_counts: Dict[str, int] = field(default_factory=dict)
    connected_peers: List[str] = field(default_factory=list)

    def add_channel(self, channel_id: str) -> None:
        """Add a channel to subscriptions."""
        self.subscribed_channels.add(channel_id)

    def remove_channel(self, channel_id: str) -> None:
        """Remove a channel from subscriptions."""
        self.subscribed_channels.discard(channel_id)

    def switch_channel(self, channel_id: str) -> bool:
        """Switch to a channel."""
        if channel_id in self.subscribed_channels:
            self.active_channel = channel_id
            self.unread_counts[channel_id] = 0  # Clear unread count
            return True
        return False

    def increment_unread(self, channel_id: str) -> None:
        """Increment unread count for a channel."""
        if channel_id not in self.unread_counts:
            self.unread_counts[channel_id] = 0
        self.unread_counts[channel_id] += 1

    def get_unread(self, channel_id: str) -> int:
        """Get unread count for a channel."""
        return self.unread_counts.get(channel_id, 0)
