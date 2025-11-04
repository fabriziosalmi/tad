"""
Unit tests for TAZCOM Gossip Protocol.

These tests focus on the gossip-specific functionality of TAZCOMNodeGossip:
- Message deduplication via msg_id
- TTL-based message forwarding
- Multi-hop message delivery
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from poc_04_gossip import TAZCOMNodeGossip


class TestMessageDeduplication:
    """Tests for duplicate message detection."""

    @pytest.mark.asyncio
    async def test_duplicate_message_is_ignored(self, initialized_gossip_node, mock_stream_reader, mock_stream_writer):
        """Test that messages with duplicate msg_id are ignored."""
        node = initialized_gossip_node

        # Create a message with specific msg_id
        message = {
            "type": "CHAT",
            "msg_id": "unique-msg-123",
            "from": "peer_id_123",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Hello!",
            "ttl": 2,
        }

        # Manually add msg_id to seen_messages
        node.seen_messages.append("unique-msg-123")

        # Setup stream to return this message
        mock_stream_reader.readuntil.return_value = (
            json.dumps(message) + "\n"
        ).encode("utf-8")

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify UI was NOT called (message was ignored)
        node.app.on_message_received.assert_not_called()

        # But ACK was still sent
        mock_stream_writer.write.assert_called()
        written_data = mock_stream_writer.write.call_args[0][0]
        assert written_data == b"ACK\n"

    @pytest.mark.asyncio
    async def test_first_message_is_processed(self, initialized_gossip_node, mock_stream_reader, mock_stream_writer):
        """Test that first occurrence of message is processed."""
        node = initialized_gossip_node

        message = {
            "type": "CHAT",
            "msg_id": "new-msg-456",
            "from": "peer_id_456",
            "timestamp": "2025-11-04T10:23:45",
            "content": "New message!",
            "ttl": 2,
        }

        mock_stream_reader.readuntil.return_value = (
            json.dumps(message) + "\n"
        ).encode("utf-8")

        # Ensure msg_id is NOT in seen_messages
        assert "new-msg-456" not in node.seen_messages

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify UI WAS called
        node.app.on_message_received.assert_called_once_with("peer_id_456", "New message!")

        # Verify msg_id was added to seen_messages
        assert "new-msg-456" in node.seen_messages


class TestMessageForwarding:
    """Tests for message forwarding logic."""

    @pytest.mark.asyncio
    async def test_message_forwarding_with_ttl_greater_than_zero(self, initialized_gossip_node):
        """Test that messages with ttl > 0 are forwarded."""
        node = initialized_gossip_node

        # Add some peers
        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
            "peer_2": {"ip": "127.0.0.3", "port": "54323", "name": "Peer 2"},
        }

        # Mock the _forward_to_peer method
        node._forward_to_peer = AsyncMock()

        # Create a message with ttl > 0
        message = {
            "type": "CHAT",
            "msg_id": "forward-test-789",
            "from": "origin_peer",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Forward me!",
            "ttl": 2,
        }

        # Call forward_message
        await node.forward_message(message, ("127.0.0.1", 54321))

        # Verify _forward_to_peer was called for each peer
        assert node._forward_to_peer.call_count == 2

        # Verify ttl was decremented
        first_call_args = node._forward_to_peer.call_args_list[0]
        forwarded_msg = first_call_args[0][2]
        assert forwarded_msg["ttl"] == 1  # Decremented from 2

    @pytest.mark.asyncio
    async def test_ttl_exhaustion_stops_forwarding(self, initialized_gossip_node):
        """Test that messages with ttl=1 are not forwarded further."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._forward_to_peer = AsyncMock()

        # Message with ttl=1 (will become 0 after decrement)
        message = {
            "type": "CHAT",
            "msg_id": "ttl-exhaustion-test",
            "from": "origin_peer",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Last hop!",
            "ttl": 1,
        }

        await node.forward_message(message, ("127.0.0.1", 54321))

        # Should NOT call _forward_to_peer (ttl becomes 0)
        node._forward_to_peer.assert_not_called()

    @pytest.mark.asyncio
    async def test_ttl_decrement(self, initialized_gossip_node):
        """Test that TTL is properly decremented during forwarding."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._forward_to_peer = AsyncMock()

        # Original message with ttl=3
        message = {
            "type": "CHAT",
            "msg_id": "ttl-decrement-test",
            "from": "origin_peer",
            "content": "Test",
            "ttl": 3,
        }

        await node.forward_message(message, ("127.0.0.1", 54321))

        # Verify ttl was decremented to 2
        call_args = node._forward_to_peer.call_args_list[0]
        forwarded_msg = call_args[0][2]
        assert forwarded_msg["ttl"] == 2


class TestMessageBroadcast:
    """Tests for message broadcasting with gossip metadata."""

    @pytest.mark.asyncio
    async def test_broadcast_generates_unique_msg_id(self, initialized_gossip_node):
        """Test that broadcast creates unique msg_id for each message."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._send_chat_message = AsyncMock()

        # Broadcast two messages
        await node.broadcast_message("Message 1")
        await node.broadcast_message("Message 2")

        # Verify two messages were sent
        assert node._send_chat_message.call_count == 2

        # Extract msg_ids from the calls
        msg_id_1 = node._send_chat_message.call_args_list[0][0][2]["msg_id"]
        msg_id_2 = node._send_chat_message.call_args_list[1][0][2]["msg_id"]

        # msg_ids should be different
        assert msg_id_1 != msg_id_2

    @pytest.mark.asyncio
    async def test_broadcast_sets_initial_ttl(self, initialized_gossip_node):
        """Test that broadcast sets initial TTL correctly."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._send_chat_message = AsyncMock()

        await node.broadcast_message("Test message")

        # Verify TTL was set
        call_args = node._send_chat_message.call_args_list[0]
        message = call_args[0][2]
        assert message["ttl"] == TAZCOMNodeGossip.INITIAL_TTL

    @pytest.mark.asyncio
    async def test_broadcast_adds_to_seen_messages(self, initialized_gossip_node):
        """Test that broadcast message is added to seen_messages."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._send_chat_message = AsyncMock()

        initial_size = len(node.seen_messages)

        await node.broadcast_message("Test message")

        # Verify msg was added to seen_messages
        assert len(node.seen_messages) == initial_size + 1

    @pytest.mark.asyncio
    async def test_broadcast_with_no_peers(self, initialized_gossip_node):
        """Test broadcast when no peers are connected."""
        node = initialized_gossip_node

        # Should not crash
        await node.broadcast_message("Message with no peers")

        # No errors should occur
        assert len(node.peers) == 0


class TestSeenMessagesCache:
    """Tests for the seen_messages deque cache."""

    @pytest.mark.asyncio
    async def test_seen_messages_max_size(self, initialized_gossip_node):
        """Test that seen_messages cache respects max size limit."""
        node = initialized_gossip_node

        # The cache has a maxlen (circular buffer behavior)
        assert node.seen_messages.maxlen == TAZCOMNodeGossip.SEEN_MESSAGES_MAX_SIZE

    def test_seen_messages_circular_buffer(self, initialized_gossip_node):
        """Test that seen_messages behaves as circular buffer."""
        node = initialized_gossip_node

        # Add messages beyond max size
        for i in range(TAZCOMNodeGossip.SEEN_MESSAGES_MAX_SIZE + 100):
            node.seen_messages.append(f"msg_{i}")

        # Cache should only contain last SEEN_MESSAGES_MAX_SIZE items
        assert len(node.seen_messages) == TAZCOMNodeGossip.SEEN_MESSAGES_MAX_SIZE

        # Oldest messages should be gone
        assert "msg_0" not in node.seen_messages
        assert "msg_99" not in node.seen_messages

        # Newest messages should be present
        assert f"msg_{TAZCOMNodeGossip.SEEN_MESSAGES_MAX_SIZE + 99}" in node.seen_messages


class TestGossipProtocolIntegration:
    """Integration tests for the gossip protocol."""

    @pytest.mark.asyncio
    async def test_new_message_is_added_to_seen_messages(
        self, initialized_gossip_node, mock_stream_reader, mock_stream_writer
    ):
        """Test that new messages are added to seen_messages."""
        node = initialized_gossip_node

        message = {
            "type": "CHAT",
            "msg_id": "integration-test-001",
            "from": "peer_id_789",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Integration test",
            "ttl": 2,
        }

        mock_stream_reader.readuntil.return_value = (
            json.dumps(message) + "\n"
        ).encode("utf-8")

        # Ensure msg_id is NOT in seen_messages initially
        assert "integration-test-001" not in node.seen_messages

        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify msg_id was added
        assert "integration-test-001" in node.seen_messages

    @pytest.mark.asyncio
    async def test_message_flow_with_gossip(self, initialized_gossip_node):
        """Test complete flow: receive message -> add to cache -> forward if needed."""
        node = initialized_gossip_node

        # Setup peer
        node.peers = {
            "peer_relay": {"ip": "127.0.0.2", "port": "54322", "name": "Relay"},
        }

        # Mock the forwarding
        node._forward_to_peer = AsyncMock()

        # Create a message that should be forwarded (ttl=2)
        message = {
            "type": "CHAT",
            "msg_id": "flow-test-001",
            "from": "origin_node",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Test flow",
            "ttl": 2,
        }

        # Simulate receiving the message
        mock_reader = AsyncMock()
        mock_writer = AsyncMock()
        mock_writer.get_extra_info.return_value = ("127.0.0.1", 54321)
        mock_reader.readuntil.return_value = (
            json.dumps(message) + "\n"
        ).encode("utf-8")

        await node.handle_connection(mock_reader, mock_writer)

        # Verify:
        # 1. Message was added to seen_messages
        assert "flow-test-001" in node.seen_messages

        # 2. UI callback was called
        node.app.on_message_received.assert_called_once_with("origin_node", "Test flow")

        # 3. Message was forwarded (ttl > 0)
        node._forward_to_peer.assert_called_once()


class TestMessageID:
    """Tests for message ID generation."""

    @pytest.mark.asyncio
    async def test_message_id_format(self, initialized_gossip_node):
        """Test that message IDs are properly formatted."""
        node = initialized_gossip_node

        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
        }

        node._send_chat_message = AsyncMock()

        await node.broadcast_message("Test message")

        # Extract msg_id from the sent message
        call_args = node._send_chat_message.call_args_list[0]
        msg_id = call_args[0][2]["msg_id"]

        # msg_id should be a string
        assert isinstance(msg_id, str)

        # msg_id should be non-empty
        assert len(msg_id) > 0

        # msg_id should be deterministic (hash-based)
        assert len(msg_id) == 16  # SHA256 truncated to 16 chars


class TestGossipShutdown:
    """Tests for graceful shutdown with gossip state."""

    @pytest.mark.asyncio
    async def test_shutdown_with_pending_forwards(self, initialized_gossip_node):
        """Test shutdown while forwarding is in progress."""
        node = initialized_gossip_node

        # Setup peers
        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322"},
        }

        # Mock _forward_to_peer to simulate pending operation
        node._forward_to_peer = AsyncMock()

        # Create a task that forwards a message
        message = {
            "type": "CHAT",
            "msg_id": "shutdown-test",
            "from": "origin",
            "content": "Test",
            "ttl": 2,
        }

        # Start forwarding (but don't wait)
        task = asyncio.create_task(node.forward_message(message, ("127.0.0.1", 54321)))

        # Shutdown
        await node.shutdown()

        # Task should complete (or be cancelled gracefully)
        try:
            await asyncio.wait_for(task, timeout=1.0)
        except asyncio.TimeoutError:
            pass  # Expected if task is still pending
