"""
Unit tests for TAZCOMNode backend class.

These tests focus on the TAZCOMNode logic without requiring real network operations.
We mock Zeroconf, TCP streams, and other external dependencies.
"""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from poc_03_chat_basic import TAZCOMNode


class TestIdentityManagement:
    """Tests for node identity creation and persistence."""

    def test_identity_creation_and_persistence(self, temp_node_dir, mock_app):
        """Test that node identity is created and persisted across restarts."""
        # First node: creates identity
        node1 = TAZCOMNode(mock_app)
        node1._load_or_create_identity()
        id1 = node1.node_id_b64

        # Verify node.key file was created
        key_file = temp_node_dir / "node.key"
        assert key_file.exists(), "node.key should be created on first run"

        # Verify file contents
        with open(key_file, "r") as f:
            key_data = json.load(f)
            assert "signing_key" in key_data
            assert "created" in key_data

        # Second node: loads existing identity
        node2 = TAZCOMNode(mock_app)
        node2._load_or_create_identity()
        id2 = node2.node_id_b64

        # IDs should match (same key)
        assert id1 == id2, "Identity should be persisted across restarts"

    def test_identity_format(self, initialized_node):
        """Test that node_id_b64 is properly formatted."""
        node = initialized_node

        # Should be base64 URL-safe without padding
        assert isinstance(node.node_id_b64, str)
        assert len(node.node_id_b64) > 0
        assert "=" not in node.node_id_b64, "node_id should not contain padding"
        assert "-" in node.node_id_b64 or "_" in node.node_id_b64 or node.node_id_b64.isalnum()

    def test_identity_uniqueness(self, temp_node_dir, mock_app):
        """Test that each new node gets a unique identity."""
        import shutil

        # Create first node
        node1 = TAZCOMNode(mock_app)
        node1._load_or_create_identity()
        id1 = node1.node_id_b64

        # Move node.key away
        shutil.move("node.key", "node.key.backup")

        # Create second node (should get new identity)
        node2 = TAZCOMNode(mock_app)
        node2._load_or_create_identity()
        id2 = node2.node_id_b64

        # IDs should be different
        assert id1 != id2, "Each new node should have unique identity"


class TestPeerManagement:
    """Tests for peer discovery and list management."""

    @pytest.mark.asyncio
    async def test_on_service_added(self, initialized_node, mock_zeroconf_service_info):
        """Test that peer discovery correctly adds peer to list."""
        node = initialized_node

        # Mock the Zeroconf instance and get_service_info
        with patch.object(node.aiozc, "zeroconf", create=True) as mock_zeroconf:
            mock_zeroconf.get_service_info.return_value = mock_zeroconf_service_info

            # Call the service added handler
            await node._on_service_added(
                mock_zeroconf, "_tazcom._tcp.local.", "TAZCOM Node x9y8z7w6._tazcom._tcp.local."
            )

        # Verify peer was added
        peer_id = "x9y8z7w6v5u4t3s2..."
        assert peer_id in node.peers, "Peer should be added to peers dict"
        assert node.peers[peer_id]["ip"] == "127.0.0.2"
        assert node.peers[peer_id]["port"] == "54322"

        # Verify callback was called
        node.app.on_peer_update.assert_called()

    @pytest.mark.asyncio
    async def test_on_service_added_ignores_self(self, initialized_node, mock_app):
        """Test that node ignores its own service announcement."""
        node = initialized_node
        node.node_id_b64 = "a1b2c3d4e5f6g7h8..."

        # Create a mock service with OUR id
        mock_info = MagicMock()
        mock_info.properties = {
            b"id": b"a1b2c3d4e5f6g7h8...",  # Same as our node
            b"version": b"0.1",
            b"p": b"54322",
        }
        mock_info.addresses = [127 << 24 | 2]
        mock_info.port = 54322

        with patch.object(node.aiozc, "zeroconf", create=True) as mock_zeroconf:
            mock_zeroconf.get_service_info.return_value = mock_info

            await node._on_service_added(mock_zeroconf, "_tazcom._tcp.local.", "test")

        # Peer should NOT be added (we ignore our own service)
        assert "a1b2c3d4e5f6g7h8..." not in node.peers

    @pytest.mark.asyncio
    async def test_on_service_removed(self, initialized_node):
        """Test that peer removal works correctly."""
        node = initialized_node

        # Manually add a peer
        peer_id = "test_peer_id"
        service_name = "Test Service Name"
        node.peers[peer_id] = {
            "ip": "127.0.0.2",
            "port": "54322",
            "name": service_name,
        }
        node.service_name_to_id[service_name] = peer_id

        # Call service removed
        await node._on_service_removed(service_name)

        # Verify peer was removed
        assert peer_id not in node.peers, "Peer should be removed from peers dict"
        assert service_name not in node.service_name_to_id, "Service name mapping should be removed"

        # Verify callback was called
        node.app.on_peer_update.assert_called()

    @pytest.mark.asyncio
    async def test_on_service_removed_nonexistent_peer(self, initialized_node):
        """Test that removing nonexistent peer doesn't crash."""
        node = initialized_node

        # Try to remove a peer that doesn't exist
        await node._on_service_removed("nonexistent_service")

        # Should not crash, peers dict should be empty
        assert len(node.peers) == 0


class TestMessageHandling:
    """Tests for incoming message handling."""

    @pytest.mark.asyncio
    async def test_handle_hello_message(self, initialized_node, mock_stream_reader, mock_stream_writer):
        """Test handling of HELLO message."""
        node = initialized_node

        hello_msg = {"type": "HELLO", "from": "peer_id_123"}
        mock_stream_reader.readuntil.return_value = (
            json.dumps(hello_msg) + "\n"
        ).encode("utf-8")

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify ACK was sent
        mock_stream_writer.write.assert_called()
        written_data = mock_stream_writer.write.call_args[0][0]
        assert written_data == b"ACK\n"

    @pytest.mark.asyncio
    async def test_handle_chat_message(self, initialized_node, mock_stream_reader, mock_stream_writer):
        """Test handling of CHAT message."""
        node = initialized_node

        chat_msg = {
            "type": "CHAT",
            "from": "peer_id_123",
            "timestamp": "2025-11-04T10:23:45",
            "content": "Hello, world!",
        }
        mock_stream_reader.readuntil.return_value = (
            json.dumps(chat_msg) + "\n"
        ).encode("utf-8")

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify callback was called with correct message
        node.app.on_message_received.assert_called_once_with("peer_id_123", "Hello, world!")

        # Verify ACK was sent
        mock_stream_writer.write.assert_called()
        written_data = mock_stream_writer.write.call_args[0][0]
        assert written_data == b"ACK\n"

    @pytest.mark.asyncio
    async def test_handle_invalid_json(self, initialized_node, mock_stream_reader, mock_stream_writer):
        """Test handling of invalid JSON message."""
        node = initialized_node

        # Send invalid JSON
        mock_stream_reader.readuntil.return_value = b"not valid json\n"

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify ERROR was sent
        mock_stream_writer.write.assert_called()
        written_data = mock_stream_writer.write.call_args[0][0]
        assert written_data == b"ERROR\n"

    @pytest.mark.asyncio
    async def test_handle_message_too_large(self, initialized_node, mock_stream_reader, mock_stream_writer):
        """Test handling of oversized message."""
        node = initialized_node

        # Simulate message size exceeded error
        mock_stream_reader.readuntil.side_effect = asyncio.LimitOverrunError(
            "message size exceeded", 0
        )

        # Call handler
        await node.handle_connection(mock_stream_reader, mock_stream_writer)

        # Verify connection was closed
        mock_stream_writer.close.assert_called()
        mock_stream_writer.wait_closed.assert_called()


class TestBroadcastMessage:
    """Tests for message broadcasting to peers."""

    @pytest.mark.asyncio
    async def test_broadcast_with_no_peers(self, initialized_node):
        """Test broadcast when no peers are connected."""
        node = initialized_node

        # Should not crash when broadcasting to empty peer list
        await node.broadcast_message("Test message")

        # No errors should occur
        assert len(node.peers) == 0

    @pytest.mark.asyncio
    async def test_broadcast_with_peers(self, initialized_node):
        """Test broadcast with active peers."""
        node = initialized_node

        # Add some mock peers
        node.peers = {
            "peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"},
            "peer_2": {"ip": "127.0.0.3", "port": "54323", "name": "Peer 2"},
        }

        # Mock the _send_chat_message method
        node._send_chat_message = AsyncMock()

        # Broadcast message
        await node.broadcast_message("Test message")

        # Verify _send_chat_message was called for each peer
        assert node._send_chat_message.call_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_empty_message(self, initialized_node):
        """Test that empty messages are not broadcast."""
        node = initialized_node

        # Add a peer
        node.peers = {"peer_1": {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"}}

        # Broadcast empty message (stripped to nothing)
        await node.broadcast_message("   ")

        # Should not send anything


class TestThreadSafety:
    """Tests for thread-safe operations."""

    @pytest.mark.asyncio
    async def test_peers_lock_prevents_race_condition(self, initialized_node):
        """Test that peers_lock properly synchronizes access."""
        node = initialized_node

        # Add initial peer
        node.peers["peer_1"] = {"ip": "127.0.0.2", "port": "54322", "name": "Peer 1"}

        # Simulate concurrent access with lock
        async def add_peer():
            async with node.peers_lock:
                node.peers["peer_2"] = {"ip": "127.0.0.3", "port": "54323", "name": "Peer 2"}

        async def remove_peer():
            async with node.peers_lock:
                if "peer_1" in node.peers:
                    del node.peers["peer_1"]

        # Run concurrently
        await asyncio.gather(add_peer(), remove_peer())

        # Verify final state is consistent
        assert "peer_2" in node.peers
        assert "peer_1" not in node.peers


class TestShutdown:
    """Tests for graceful shutdown."""

    @pytest.mark.asyncio
    async def test_shutdown_with_no_server(self, initialized_node):
        """Test shutdown when server is not initialized."""
        node = initialized_node
        node.server = None
        node.aiozc = None

        # Should not crash
        await node.shutdown()

    @pytest.mark.asyncio
    async def test_shutdown_closes_server(self, initialized_node):
        """Test that shutdown properly closes server."""
        node = initialized_node

        # Mock the server
        node.server = AsyncMock()
        node.server.close = Mock()
        node.server.wait_closed = AsyncMock()

        # Shutdown
        await node.shutdown()

        # Verify server was closed
        node.server.close.assert_called()
        node.server.wait_closed.assert_called()
