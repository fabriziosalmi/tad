"""
Pytest configuration and shared fixtures for TAZCOM tests.

This file provides:
- Mock app fixtures for testing TAZCOMNode in isolation
- Temporary directory fixtures for avoiding test pollution
- Async support configuration
"""

import asyncio
import json
import socket
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

# Make asyncio event loop available to all async tests
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
def mock_app():
    """
    Create a mock TAZCOMChatApp for testing TAZCOMNode in isolation.

    This mock provides all the callback methods that TAZCOMNode expects.
    """
    app = MagicMock()
    app.on_peer_update = MagicMock()
    app.on_message_received = MagicMock()
    return app


@pytest.fixture
def temp_node_dir(tmp_path, monkeypatch):
    """
    Create a temporary directory for node.key files during tests.

    This prevents test pollution and node.key conflicts between test runs.
    """
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def initialized_node(mock_app, temp_node_dir):
    """
    Create and initialize a TAZCOMNode with mocked app.

    This fixture:
    1. Creates a TAZCOMNode with mock app
    2. Initializes identity (creates node.key)
    3. Yields the node for testing
    4. Cleans up resources on teardown

    Note: Does NOT initialize TCP server or Zeroconf to avoid real network ops.
    """
    # Import here to avoid circular imports
    from poc_03_chat_basic import TAZCOMNode

    node = TAZCOMNode(mock_app)

    # Initialize identity (this is safe, no network ops)
    node._load_or_create_identity()

    # Manually set event loop
    node.event_loop = asyncio.get_event_loop()

    # Allocate a port for testing
    node.tcp_port = _allocate_test_port()
    node.local_ip = "127.0.0.1"

    # Set up empty peers dict for testing
    node.peers = {}
    node.service_name_to_id = {}

    yield node

    # Cleanup: Close server if it exists
    if node.server:
        try:
            node.server.close()
            # For sync fixtures, we can't await, so schedule the coroutine on the event loop
            try:
                asyncio.get_event_loop().run_until_complete(node.server.wait_closed())
            except Exception:
                pass
        except Exception:
            pass

    # Cleanup: Close Zeroconf if it exists
    if node.aiozc:
        try:
            try:
                asyncio.get_event_loop().run_until_complete(node.aiozc.async_close())
            except Exception:
                pass
        except Exception:
            pass


@pytest.fixture
def initialized_gossip_node(mock_app, temp_node_dir):
    """
    Create and initialize a TAZCOMNodeGossip with mocked app.

    This fixture:
    1. Creates a TAZCOMNodeGossip with mock app
    2. Initializes identity (creates node.key)
    3. Yields the node for testing
    4. Cleans up resources on teardown

    Note: Does NOT initialize TCP server or Zeroconf to avoid real network ops.
    """
    # Import here to avoid circular imports
    from poc_04_gossip import TAZCOMNodeGossip

    node = TAZCOMNodeGossip(mock_app)

    # Initialize identity (this is safe, no network ops)
    node._load_or_create_identity()

    # Manually set event loop
    node.event_loop = asyncio.get_event_loop()

    # Allocate a port for testing
    node.tcp_port = _allocate_test_port()
    node.local_ip = "127.0.0.1"

    # Set up empty peers dict for testing
    node.peers = {}
    node.service_name_to_id = {}

    yield node

    # Cleanup: Close server if it exists
    if node.server:
        try:
            node.server.close()
            # For sync fixtures, we can't await, so schedule the coroutine on the event loop
            try:
                asyncio.get_event_loop().run_until_complete(node.server.wait_closed())
            except Exception:
                pass
        except Exception:
            pass

    # Cleanup: Close Zeroconf if it exists
    if node.aiozc:
        try:
            try:
                asyncio.get_event_loop().run_until_complete(node.aiozc.async_close())
            except Exception:
                pass
        except Exception:
            pass


@pytest.fixture
def mock_stream_reader():
    """
    Create a mock asyncio.StreamReader for testing TCP message handling.
    """
    reader = AsyncMock()
    return reader


@pytest.fixture
def mock_stream_writer():
    """
    Create a mock asyncio.StreamWriter for testing TCP message handling.
    """
    writer = AsyncMock()
    writer.get_extra_info = Mock(return_value=("127.0.0.1", 54321))
    writer.write = Mock()
    writer.drain = AsyncMock()
    writer.close = Mock()
    writer.wait_closed = AsyncMock()
    return writer


@pytest.fixture
def mock_zeroconf_service_info():
    """
    Create a mock Zeroconf ServiceInfo object.

    Used to simulate service discovery events.
    """
    info = MagicMock()
    info.properties = {
        b"id": b"x9y8z7w6v5u4t3s2...",
        b"version": b"0.1",
        b"p": b"54322",
    }
    info.addresses = [socket.inet_aton("127.0.0.2")]
    info.port = 54322
    return info


def _allocate_test_port() -> int:
    """
    Allocate an available TCP port for testing.

    Uses the same approach as the actual code: bind to port 0 and let the OS assign.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        s.listen(1)
        _, port = s.getsockname()
    return port


@pytest.fixture
def chat_message() -> dict:
    """
    Provide a valid CHAT message for testing.
    """
    return {
        "type": "CHAT",
        "from": "a1b2c3d4e5f6g7h8...",
        "timestamp": "2025-11-04T10:23:45.123456",
        "content": "Hello, this is a test message!",
    }


@pytest.fixture
def hello_message() -> dict:
    """
    Provide a valid HELLO message for testing.
    """
    return {
        "type": "HELLO",
        "from": "a1b2c3d4e5f6g7h8...",
    }


# Configure asyncio event loop policy for tests
@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.

    This ensures all async tests use the same event loop.
    """
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()
