"""
Test Suite for Milestone 6: Secure & Private Channels

Tests the implementation of:
- Private channel creation and key generation
- Secure invitation flow using asymmetric encryption (SealedBox)
- End-to-end encrypted (E2EE) messaging within private channels
- Security model enforcement (non-members cannot read messages)
- Role-based permissions for invitations
"""

import asyncio
import pytest
import random
from typing import Dict, List

from tad.node import TADNode
from tad.crypto.e2ee import E2EEManager

# Helper to create and start a node
async def create_and_start_node(username: str) -> TADNode:
    """Factory to create and fully start a TADNode."""
    unique_username = f"{username}-{random.randint(1000, 9999)}"
    profile_path = f"{unique_username}_profile.json"
    node = TADNode(username=unique_username, db_path=f":memory:", profile_path=profile_path)
    await node.start()
    # Allow time for services to initialize
    await asyncio.sleep(0.2) # Increased delay
    return node

@pytest.mark.asyncio
async def test_private_channel_creation():
    """
    Verify that creating a private channel correctly generates a key
    and sets the owner in the database.
    """
    node_A = await create_and_start_node("NodeA")
    channel_id = "#private-test"

    # 1. Create a private channel
    success = node_A.create_channel(channel_id, channel_type="private")
    assert success, "Channel creation should succeed"

    # 2. Verify key was generated and stored
    assert node_A.e2ee_manager.has_channel_key(
        channel_id
    ), "Node A should have the key for the channel it created"
    channel_key = node_A.e2ee_manager.get_channel_key(channel_id)
    assert isinstance(channel_key, bytes) and len(channel_key) == 32

    # 3. Verify database state
    channel_info = node_A.db_manager.get_channel_info(channel_id)
    assert channel_info is not None, "Channel should be in the database"
    assert channel_info["type"] == "private", "Channel type should be private"
    assert (
        channel_info["owner_node_id"] == node_A.node_id_b64
    ), "Node A should be the owner"

    # 4. Verify owner is a member
    assert node_A.db_manager.is_channel_member(
        channel_id, node_A.node_id_b64
    ), "Owner should be a member of the channel"
    
    await node_A.stop()

@pytest.mark.asyncio
async def test_invite_flow_end_to_end():
    """
    Tests the full invite flow:
    1. Node A creates a private channel.
    2. Node A invites Node B.
    3. Node B receives the invite, decrypts the key, and joins.
    """
    node_A = await create_and_start_node("NodeA")
    node_B = await create_and_start_node("NodeB")
    channel_id = "#secure-chat"

    # Mock message reception for Node B
    received_messages: List[Dict] = []

    async def on_message_b(message):
        received_messages.append(message)

    node_B.on_message_received = on_message_b

    # 1. Node A creates the channel
    node_A.create_channel(channel_id, channel_type="private")

    # 2. Node A invites Node B
    await node_A.invite_peer_to_channel(channel_id, node_B.node_id_b64, node_B.identity.encryption_public_key_hex)
    await asyncio.sleep(0.1) # Allow async processing

@pytest.mark.asyncio
async def test_e2ee_messaging():
    """
    Tests that messages sent in a private channel are correctly
    encrypted and decrypted by members.
    """
    node_A = await create_and_start_node("NodeA")
    node_B = await create_and_start_node("NodeB")
    channel_id = "#e2ee-test"
    secret_message = "The eagle flies at midnight."

    # Setup: Node A creates channel and invites Node B
    node_A.create_channel(channel_id, channel_type="private")
    await node_A.invite_peer_to_channel(channel_id, node_B.node_id_b64, node_B.identity.encryption_public_key_hex)
    await asyncio.sleep(0.1)

    # Mock message reception for Node B
    decrypted_msg_content = None
    callback_event = asyncio.Event()

    async def on_message_b(message: dict):
        nonlocal decrypted_msg_content
        # The callback receives the payload dict with decrypted "content"
        decrypted_msg_content = message.get("content")
        callback_event.set()

    node_B.on_message_received = on_message_b

    # 1. Node A broadcasts the secret message
    # The broadcast_message method should handle encryption automatically
    msg_id = await node_A.broadcast_message(secret_message, channel_id)

    # 2. Retrieve the stored message to get the encrypted content
    stored_messages = node_A.db_manager.get_messages_for_channel(channel_id, 1)
    assert len(stored_messages) > 0, "Message should be stored in Node A's DB"

    stored_msg = stored_messages[0]

    # 3. Create a gossip-formatted message (with payload wrapper) for Node B
    # This simulates what would come from the gossip protocol
    gossip_message = {
        "msg_id": stored_msg.get("msg_id"),
        "sender_id": node_A.node_id_b64,
        "signature": stored_msg.get("signature", ""),
        "payload": {
            "content": stored_msg.get("content"),  # This is encrypted for private channels
            "channel_id": channel_id,
            "nonce": stored_msg.get("nonce"),  # For private channels
            "is_encrypted": stored_msg.get("is_encrypted", False),
        }
    }

    # 4. Simulate gossip to Node B
    await node_B._on_gossip_message_received(gossip_message)

    # 5. Wait for callback to complete (private channels use asyncio.create_task)
    try:
        await asyncio.wait_for(callback_event.wait(), timeout=2.0)
    except asyncio.TimeoutError:
        pass  # Callback might not have been invoked

    # 6. Assert Node B decrypted the message correctly
    assert decrypted_msg_content is not None, "Node B should have received a message"
    assert decrypted_msg_content == secret_message, "Decrypted message content should match the original"
    
    await node_A.stop()
    await node_B.stop()

@pytest.mark.asyncio
async def test_non_member_cannot_read_messages():
    """
    CRITICAL: Ensures a non-member (Node C) cannot read messages
    sent to a private channel.
    """
    node_A = await create_and_start_node("NodeA")
    node_B = await create_and_start_node("NodeB")
    node_C = await create_and_start_node("NodeC")
    channel_id = "#top-secret"
    secret_message = "Project Chimera is a go."

    # Setup: Node A creates channel and invites Node B
    node_A.create_channel(channel_id, channel_type="private")
    await node_A.invite_peer_to_channel(channel_id, node_B.node_id_b64, node_B.identity.encryption_public_key_hex)
    await asyncio.sleep(0.1)

    # Mock message reception for Node C
    node_c_messages = []
    async def on_message_c(message):
        node_c_messages.append(message)
    node_C.on_message_received = on_message_c

    # 1. Node A broadcasts the message
    msg_id = await node_A.broadcast_message(secret_message, channel_id)
    raw_msg = node_A.db_manager.get_messages_for_channel(channel_id, 1)[0]

    # 2. Simulate gossip to Node C (non-member)
    # The message handler in Node C should silently drop the message
    await node_C._on_gossip_message_received(raw_msg)
    await asyncio.sleep(0.1)

    # 3. Assert Node C did NOT receive or process the message
    assert not node_C.e2ee_manager.has_channel_key(
        channel_id
    ), "Node C should not have the key"
    assert (
        len(node_c_messages) == 0
    ), "Node C should not have any messages in its UI/callback list"
    assert (
        node_C.db_manager.get_message_count(channel_id) == 0
    ), "Node C should not store the message in its database"
    
    await node_A.stop()
    await node_B.stop()
    await node_C.stop()

@pytest.mark.asyncio
async def test_invite_permissions():
    """
    Tests that a non-owner node cannot invite others to a private channel.
    """
    node_A = await create_and_start_node("NodeA")
    node_B = await create_and_start_node("NodeB")
    node_C = await create_and_start_node("NodeC")
    channel_id = "#exclusive"

    # Setup: Node A creates channel and invites Node B
    node_A.create_channel(channel_id, channel_type="private")
    await node_A.invite_peer_to_channel(channel_id, node_B.node_id_b64, node_B.identity.encryption_public_key_hex)
    await asyncio.sleep(0.1)

    # 1. Node B (a member, but not owner) tries to invite Node C
    # This should fail silently or log a warning on Node B's side.
    await node_B.invite_peer_to_channel(channel_id, node_C.node_id_b64, node_C.identity.encryption_public_key_hex)
    await asyncio.sleep(0.1)

    # 2. Assert that Node C did NOT get an invite or join the channel
    assert not node_C.e2ee_manager.has_channel_key(
        channel_id
    ), "Node C should not have the key after a failed invite"
    assert not node_C.db_manager.is_channel_member(
        channel_id, node_C.node_id_b64
    ), "Node C should not be a member of the channel"

    await node_A.stop()
    await node_B.stop()
    await node_C.stop()