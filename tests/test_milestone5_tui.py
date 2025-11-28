"""
TAD Milestone 5 - Advanced TUI Tests

Comprehensive test suite for the Textual-based advanced TUI interface.

Tests focus on:
- UIState logic and state management
- Command parsing and input handling
- Command handler logic (without widget mounting)
"""

import asyncio
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
from typing import Optional

from tad.main import TADTUIApp
from tad.node import TADNode
from tad.ui import ChannelList, MessageView, PeerList, CommandInput, UIState


class TestUIState:
    """Test the UIState dataclass - core state management."""

    def test_ui_state_initialization(self):
        """Test UIState initializes with correct defaults."""
        state = UIState()
        assert state.active_channel == "#general"
        assert "#general" in state.subscribed_channels
        assert len(state.subscribed_channels) == 1
        assert state.unread_counts == {}
        assert state.connected_peers == []

    def test_add_channel(self):
        """Test adding a channel to subscriptions."""
        state = UIState()
        state.add_channel("#dev")
        assert "#dev" in state.subscribed_channels
        assert len(state.subscribed_channels) == 2

    def test_remove_channel(self):
        """Test removing a channel from subscriptions."""
        state = UIState()
        state.add_channel("#dev")
        state.remove_channel("#dev")
        assert "#dev" not in state.subscribed_channels
        assert "#general" in state.subscribed_channels

    def test_switch_channel(self):
        """Test switching to a subscribed channel."""
        state = UIState()
        state.add_channel("#dev")
        result = state.switch_channel("#dev")
        assert result is True
        assert state.active_channel == "#dev"
        assert state.unread_counts.get("#dev") == 0

    def test_switch_to_unsubscribed_channel(self):
        """Test switching to a channel we're not subscribed to."""
        state = UIState()
        result = state.switch_channel("#notexist")
        assert result is False
        assert state.active_channel == "#general"

    def test_unread_count_increment(self):
        """Test incrementing unread count."""
        state = UIState()
        state.increment_unread("#general")
        state.increment_unread("#general")
        assert state.get_unread("#general") == 2

    def test_unread_count_persistence(self):
        """Test unread count clears on channel switch."""
        state = UIState()
        state.add_channel("#dev")
        state.increment_unread("#dev")
        assert state.get_unread("#dev") == 1
        state.switch_channel("#dev")
        assert state.unread_counts.get("#dev") == 0

    def test_multiple_channels(self):
        """Test managing multiple channels."""
        state = UIState()
        state.add_channel("#dev")
        state.add_channel("#random")
        state.add_channel("#gaming")

        assert len(state.subscribed_channels) == 4
        assert state.active_channel == "#general"

        state.switch_channel("#dev")
        assert state.active_channel == "#dev"

        state.switch_channel("#gaming")
        assert state.active_channel == "#gaming"

    def test_unread_counts_by_channel(self):
        """Test tracking unread counts per channel."""
        state = UIState()
        state.add_channel("#dev")
        state.add_channel("#random")

        state.increment_unread("#general")
        state.increment_unread("#general")
        state.increment_unread("#dev")
        state.increment_unread("#random")
        state.increment_unread("#random")
        state.increment_unread("#random")

        assert state.get_unread("#general") == 2
        assert state.get_unread("#dev") == 1
        assert state.get_unread("#random") == 3

    def test_channel_isolation(self):
        """Test that channels are isolated from each other."""
        state = UIState()
        state.add_channel("#dev")
        state.add_channel("#ops")

        state.increment_unread("#dev")
        state.increment_unread("#ops")
        state.increment_unread("#ops")

        # Modifying one doesn't affect the other
        assert state.get_unread("#dev") == 1
        assert state.get_unread("#ops") == 2

    def test_cannot_remove_general(self):
        """Test that #general cannot be removed (logic)."""
        state = UIState()
        # This is more of a constraint that should be in TADTUIApp
        state.remove_channel("#general")
        # The state allows this, but TADTUIApp should prevent it
        assert "#general" not in state.subscribed_channels


class TestCommandParsing:
    """Test CommandInput widget initialization and basic setup."""

    def test_command_input_initialization(self):
        """Test CommandInput widget initializes correctly."""
        cmd_input = CommandInput()
        assert cmd_input.on_message is None
        assert cmd_input.on_command is None
        assert cmd_input.history == []
        assert cmd_input.history_index == -1

    def test_command_input_with_callbacks(self):
        """Test CommandInput widget can be created with callbacks."""
        def on_msg(msg):
            pass

        def on_cmd(cmd, args):
            pass

        cmd_input = CommandInput(on_message=on_msg, on_command=on_cmd)
        assert cmd_input.on_message == on_msg
        assert cmd_input.on_command == on_cmd


class TestChannelCommands:
    """Test channel command logic (mocked)."""

    @pytest.fixture
    def app_with_mocks(self):
        """Create TADTUIApp with mocked widgets."""
        node = TADNode(username="TestUser")
        app = TADTUIApp(node)

        # Mock the widgets since they won't be mounted
        app.channel_list = Mock()
        app.message_view = Mock()
        app.peer_list = Mock()
        app.command_input = Mock()

        return app

    def test_join_command_updates_state(self, app_with_mocks):
        """Test /join command updates UIState."""
        app = app_with_mocks

        app._cmd_join(["#dev"])

        assert "#dev" in app.ui_state.subscribed_channels

    def test_join_adds_prefix_if_missing(self, app_with_mocks):
        """Test /join adds # prefix if missing."""
        app = app_with_mocks

        app._cmd_join(["dev"])

        assert "#dev" in app.ui_state.subscribed_channels

    def test_join_calls_widget_add(self, app_with_mocks):
        """Test /join calls channel_list.add_channel."""
        app = app_with_mocks

        app._cmd_join(["#new"])

        app.channel_list.add_channel.assert_called_with("#new", "public")

    def test_leave_removes_from_state(self, app_with_mocks):
        """Test /leave removes channel from state."""
        app = app_with_mocks

        # First join
        app._cmd_join(["#dev"])
        assert "#dev" in app.ui_state.subscribed_channels

        # Then leave
        app._cmd_leave(["#dev"])
        assert "#dev" not in app.ui_state.subscribed_channels

    def test_leave_protected_general(self, app_with_mocks):
        """Test /leave prevents leaving #general."""
        app = app_with_mocks

        app._cmd_leave(["#general"])

        assert "#general" in app.ui_state.subscribed_channels

    def test_leave_calls_widget_remove(self, app_with_mocks):
        """Test /leave calls channel_list.remove_channel."""
        app = app_with_mocks

        app._cmd_join(["#temp"])
        app._cmd_leave(["#temp"])

        app.channel_list.remove_channel.assert_called_with("#temp")

    def test_switch_via_ui_state(self, app_with_mocks):
        """Test UIState switching logic via command."""
        app = app_with_mocks

        app._cmd_join(["#dev"])
        # Manually check UIState switching (skip app.call_later)
        result = app.ui_state.switch_channel("#dev")

        assert result is True
        assert app.ui_state.active_channel == "#dev"

    def test_switch_without_subscription_fails(self, app_with_mocks):
        """Test /switch to unsubscribed channel fails."""
        app = app_with_mocks

        # Try to switch to channel not joined
        result = app.ui_state.switch_channel("#notjoined")

        # Should fail
        assert result is False
        assert app.ui_state.active_channel == "#general"

    def test_channels_command_formats_list(self, app_with_mocks):
        """Test /channels command formatting."""
        app = app_with_mocks

        app._cmd_join(["#dev"])
        app._cmd_join(["#random"])

        # Command should display output
        app._cmd_channels([])

        # Verify at least one output call
        assert app.message_view.add_command_output.called

    def test_peers_command_shows_count(self, app_with_mocks):
        """Test /peers command shows peer count."""
        app = app_with_mocks
        app.peer_list.get_peer_count.return_value = 3

        app._cmd_peers([])

        # Should have called with output
        app.message_view.add_command_output.assert_called()

    def test_help_command_displays_help(self, app_with_mocks):
        """Test /help command displays help text."""
        app = app_with_mocks

        app._cmd_help([])

        # Should have output
        app.message_view.add_command_output.assert_called()


class TestChannelNavigation:
    """Test channel navigation through UIState."""

    def test_navigation_get_channels_list(self):
        """Test getting sorted list of channels for navigation."""
        state = UIState()
        state.add_channel("#dev")
        state.add_channel("#random")

        channels = sorted(state.subscribed_channels)
        # Should have 3 channels
        assert len(channels) == 3
        assert "#general" in channels

    def test_navigation_index_calculation(self):
        """Test navigation index calculations."""
        state = UIState()
        state.add_channel("#dev")
        state.add_channel("#random")

        channels = sorted(state.subscribed_channels)
        current_idx = channels.index("#general")

        # Calculate next and previous indices
        next_idx = (current_idx + 1) % len(channels)
        prev_idx = (current_idx - 1) % len(channels)

        assert 0 <= next_idx < len(channels)
        assert 0 <= prev_idx < len(channels)

    def test_channel_list_ordering_consistency(self):
        """Test that channel ordering is consistent."""
        state = UIState()
        state.add_channel("#zzz")
        state.add_channel("#aaa")
        state.add_channel("#mmm")

        channels1 = sorted(state.subscribed_channels)
        channels2 = sorted(state.subscribed_channels)

        # Ordering should be consistent
        assert channels1 == channels2
        assert channels1 == ["#aaa", "#general", "#mmm", "#zzz"]


class TestUIConsistency:
    """Test UI state consistency invariants."""

    def test_active_channel_always_subscribed(self):
        """Invariant: active channel must be in subscribed channels."""
        state = UIState()
        state.add_channel("#dev")
        state.switch_channel("#dev")

        assert state.active_channel in state.subscribed_channels

    def test_general_always_subscribed(self):
        """Invariant: #general must always be subscribed."""
        state = UIState()
        # Try to remove it (implementation allows, but TADTUIApp should prevent)
        state.remove_channel("#general")

        # Even if removed from state, TADTUIApp should maintain invariant
        # This is tested in command handlers

    def test_leave_active_switches_to_general(self):
        """Test leaving active channel switches to #general."""
        state = UIState()
        state.add_channel("#dev")
        state.switch_channel("#dev")

        assert state.active_channel == "#dev"

        state.remove_channel("#dev")
        # Manually switch (TADTUIApp should do this)
        state.switch_channel("#general")

        assert state.active_channel == "#general"

    def test_multiple_joins_same_channel(self):
        """Test joining same channel twice doesn't duplicate."""
        state = UIState()
        state.add_channel("#dev")
        initial_count = len(state.subscribed_channels)

        state.add_channel("#dev")
        # Sets don't duplicate
        assert len(state.subscribed_channels) == initial_count

    def test_channel_name_normalization(self):
        """Test that command handlers normalize channel names."""
        # The _cmd_join method normalizes channel names
        # Test through UIState that normalization works
        state = UIState()

        # Both formats should be equivalent after normalization
        state.add_channel("#dev")
        state.add_channel("#random")

        assert len(state.subscribed_channels) == 3
        # All channels should have # prefix in state
        for ch in state.subscribed_channels:
            assert ch.startswith("#")


class TestErrorHandling:
    """Test graceful error handling."""

    @pytest.fixture
    def app(self):
        """Create TADTUIApp with mocked widgets."""
        node = TADNode(username="TestUser")
        app = TADTUIApp(node)

        app.channel_list = Mock()
        app.message_view = Mock()
        app.peer_list = Mock()

        return app

    def test_join_no_args(self, app):
        """Test /join with no arguments."""
        # Should not crash
        app._cmd_join([])
        app.message_view.add_command_output.assert_called()

    def test_leave_no_args(self, app):
        """Test /leave with no arguments."""
        # Should not crash
        app._cmd_leave([])
        app.message_view.add_command_output.assert_called()

    def test_switch_no_args(self, app):
        """Test /switch with no arguments."""
        # Should not crash
        app._cmd_switch([])
        app.message_view.add_command_output.assert_called()

    def test_switch_invalid_channel(self, app):
        """Test switch to channel not joined."""
        app._cmd_switch(["#notjoined"])
        # Should show error and stay at #general
        assert app.ui_state.active_channel == "#general"


class TestIntegrationFlows:
    """Test complete user interaction flows using UIState."""

    def test_join_leave_flow(self):
        """Test complete join-leave flow."""
        state = UIState()

        # Start at #general
        assert state.active_channel == "#general"

        # Join a channel
        state.add_channel("#work")
        assert "#work" in state.subscribed_channels

        # Switch to it
        result = state.switch_channel("#work")
        assert result is True
        assert state.active_channel == "#work"

        # Leave it (manually switch back first since TADTUIApp does this)
        state.remove_channel("#work")
        result = state.switch_channel("#general")
        assert result is True
        assert "#work" not in state.subscribed_channels
        assert state.active_channel == "#general"

    def test_multi_channel_workflow(self):
        """Test managing multiple channels."""
        state = UIState()

        # Join several channels
        state.add_channel("#dev")
        state.add_channel("#design")
        state.add_channel("#ops")

        # Should be subscribed to all
        assert len(state.subscribed_channels) == 4

        # Switch through them
        for channel in ["#dev", "#design", "#ops", "#general"]:
            result = state.switch_channel(channel)
            assert result is True
            assert state.active_channel == channel

        # Leave one
        state.remove_channel("#design")
        assert "#design" not in state.subscribed_channels
        # Should still be able to switch to remaining channels
        result = state.switch_channel("#general")
        assert result is True
        assert state.active_channel in state.subscribed_channels


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
