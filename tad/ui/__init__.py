"""
TAD Advanced TUI Module (Milestone 5)

Provides custom Textual widgets and components for a modern, multi-channel interface.

Components:
- ChannelList: Display and manage subscribed channels
- PeerList: Show active peers in selected channel
- MessageView: Display message history with formatting
- CommandInput: Parse and handle user commands
"""

from .widgets import ChannelList, CommandInput, MessageView, PeerList, UIState

__all__ = ["ChannelList", "PeerList", "MessageView", "CommandInput", "UIState"]
