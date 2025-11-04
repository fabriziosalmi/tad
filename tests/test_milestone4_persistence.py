"""
Milestone 4: Message Persistence Test Suite

Tests for SQLite-based message storage and retrieval.

Test Coverage:
- Database schema creation
- Message storage with duplicate prevention
- Message retrieval with ordering and limits
- Channel management
- Integration with TADNode
- Node restart persistence
"""

import asyncio
import json
import os
import sqlite3
from pathlib import Path
from typing import Dict

import pytest

from tad.node import TADNode
from tad.persistence import DatabaseManager


class TestDatabaseManager:
    """Tests for DatabaseManager class."""

    def test_database_initialization(self, tmp_path):
        """Test that DatabaseManager initializes and creates database file."""
        db_path = tmp_path / "test.db"
        db = DatabaseManager(db_path=str(db_path))

        # Database file should exist
        assert db_path.exists()
        logger.info("✓ Database file created")

        db.close()

    def test_table_creation(self, tmp_path):
        """Test that DatabaseManager creates correct tables and schema."""
        db_path = tmp_path / "test_tables.db"
        db = DatabaseManager(db_path=str(db_path))

        # Connect directly to verify tables exist
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check channels table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='channels'"
        )
        assert cursor.fetchone() is not None, "channels table not found"
        logger.info("✓ channels table created")

        # Check messages table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        assert cursor.fetchone() is not None, "messages table not found"
        logger.info("✓ messages table created")

        # Verify foreign key constraint
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]
        assert "channel_id" in columns
        assert "msg_id" in columns
        assert "sender_id" in columns
        logger.info("✓ Table schema correct")

        conn.close()
        db.close()

    def test_store_and_retrieve_message(self, tmp_path):
        """Test storing a message and retrieving it."""
        db = DatabaseManager(db_path=str(tmp_path / "test_store.db"))

        # Create test message
        test_message = {
            "msg_id": "test_msg_001",
            "payload": {
                "channel_id": "#general",
                "type": "chat_message",
                "content": "Hello, World!",
                "timestamp": "2025-11-04T12:00:00",
            },
            "sender_id": "abc123def456abc123def456abc123def456abc123def456abc123def456abcd",
            "signature": "sig_test_001",
        }

        # Store message
        stored = db.store_message(test_message)
        assert stored is True, "Failed to store message"
        logger.info("✓ Message stored successfully")

        # Retrieve message
        messages = db.get_messages_for_channel("#general")
        assert len(messages) == 1
        assert messages[0]["msg_id"] == "test_msg_001"
        assert messages[0]["content"] == "Hello, World!"
        logger.info("✓ Message retrieved correctly")

        db.close()

    def test_duplicate_message_ignored(self, tmp_path):
        """Test that storing the same message twice doesn't create duplicates."""
        db = DatabaseManager(db_path=str(tmp_path / "test_dup.db"))

        test_message = {
            "msg_id": "dup_test_001",
            "payload": {
                "channel_id": "#general",
                "type": "chat_message",
                "content": "Duplicate test",
                "timestamp": "2025-11-04T12:01:00",
            },
            "sender_id": "sender123",
            "signature": "sig_dup_001",
        }

        # Store twice
        stored1 = db.store_message(test_message)
        stored2 = db.store_message(test_message)

        assert stored1 is True, "First insertion should succeed"
        assert stored2 is False, "Duplicate insertion should be ignored"
        logger.info("✓ Duplicate insertion correctly ignored")

        # Verify only one message in database
        messages = db.get_messages_for_channel("#general")
        assert len(messages) == 1
        logger.info("✓ Database contains only one copy")

        db.close()

    def test_get_messages_ordering_and_limit(self, tmp_path):
        """Test that messages are returned in correct order with limit respected."""
        db = DatabaseManager(db_path=str(tmp_path / "test_order.db"))

        # Store multiple messages
        for i in range(10):
            message = {
                "msg_id": f"msg_{i:03d}",
                "payload": {
                    "channel_id": "#general",
                    "type": "chat_message",
                    "content": f"Message {i}",
                    "timestamp": f"2025-11-04T12:{i:02d}:00",
                },
                "sender_id": "sender",
                "signature": f"sig_{i}",
            }
            db.store_message(message)

        logger.info("✓ 10 messages stored")

        # Retrieve with limit
        messages = db.get_messages_for_channel("#general", last_n=5)
        assert len(messages) == 5, f"Expected 5 messages, got {len(messages)}"
        logger.info("✓ Limit parameter respected")

        # Verify ordering (should be oldest first)
        for i, msg in enumerate(messages):
            expected_content = f"Message {i + 5}"
            assert msg["content"] == expected_content, (
                f"Expected '{expected_content}', got '{msg['content']}'"
            )
        logger.info("✓ Messages in correct chronological order")

        db.close()

    def test_channel_management(self, tmp_path):
        """Test storing and retrieving channels."""
        db = DatabaseManager(db_path=str(tmp_path / "test_channels.db"))

        # Store channels
        db.store_channel("#general", "General Discussion")
        db.store_channel("#dev", "Development")
        db.store_channel("#random", "Random Topics")

        logger.info("✓ Channels stored")

        # Retrieve channels
        channels = db.get_all_channels()
        assert len(channels) == 3
        channel_ids = {ch["channel_id"] for ch in channels}
        assert channel_ids == {"#general", "#dev", "#random"}
        logger.info("✓ All channels retrieved correctly")

        db.close()

    def test_message_count(self, tmp_path):
        """Test message counting functionality."""
        db = DatabaseManager(db_path=str(tmp_path / "test_count.db"))

        # Add messages to different channels
        for i in range(5):
            msg = {
                "msg_id": f"general_{i}",
                "payload": {
                    "channel_id": "#general",
                    "type": "chat_message",
                    "content": f"Msg {i}",
                    "timestamp": f"2025-11-04T12:{i:02d}:00",
                },
                "sender_id": "sender",
                "signature": f"sig_{i}",
            }
            db.store_message(msg)

        for i in range(3):
            msg = {
                "msg_id": f"dev_{i}",
                "payload": {
                    "channel_id": "#dev",
                    "type": "chat_message",
                    "content": f"Dev {i}",
                    "timestamp": f"2025-11-04T13:{i:02d}:00",
                },
                "sender_id": "sender",
                "signature": f"sig_dev_{i}",
            }
            db.store_message(msg)

        # Test total count
        total = db.get_message_count()
        assert total == 8, f"Expected 8 total messages, got {total}"
        logger.info(f"✓ Total message count correct: {total}")

        # Test per-channel count
        general_count = db.get_message_count("#general")
        assert general_count == 5
        dev_count = db.get_message_count("#dev")
        assert dev_count == 3
        logger.info(f"✓ Per-channel counts correct: #general={general_count}, #dev={dev_count}")

        db.close()


class TestTADNodeIntegration:
    """Integration tests with TADNode."""

    @pytest.mark.asyncio
    async def test_node_persists_messages(self, tmp_path):
        """Test that TADNode saves messages to database."""
        db_path = tmp_path / "test_node.db"

        # Create and start node
        node = TADNode(db_path=str(db_path))

        # Create a test message as if it were received
        test_message = {
            "msg_id": "integration_test_001",
            "payload": {
                "channel_id": "#general",
                "type": "chat_message",
                "content": "Integration test message",
                "timestamp": "2025-11-04T12:00:00",
            },
            "sender_id": "integration_test_sender",
            "signature": "integration_test_sig",
        }

        # Store message via node's database manager
        stored = node.db_manager.store_message(test_message)
        assert stored is True
        logger.info("✓ Message persisted via TADNode.db_manager")

        # Retrieve via node's API
        history = await node.load_channel_history("#general")
        assert len(history) == 1
        assert history[0]["msg_id"] == "integration_test_001"
        logger.info("✓ Message retrieved via TADNode.load_channel_history()")

        # Close connection
        node.db_manager.close()

    @pytest.mark.asyncio
    async def test_persistence_across_restart(self, tmp_path):
        """Test that messages persist across node restart."""
        db_path = tmp_path / "test_restart.db"

        # First node instance
        node1 = TADNode(db_path=str(db_path))

        message1 = {
            "msg_id": "restart_test_001",
            "payload": {
                "channel_id": "#general",
                "type": "chat_message",
                "content": "Message before restart",
                "timestamp": "2025-11-04T12:00:00",
            },
            "sender_id": "sender1",
            "signature": "sig1",
        }

        node1.db_manager.store_message(message1)
        logger.info("✓ Message stored in first node instance")

        node1.db_manager.close()

        # Second node instance (restart simulation)
        node2 = TADNode(db_path=str(db_path))

        history = await node2.load_channel_history("#general")
        assert len(history) == 1
        assert history[0]["content"] == "Message before restart"
        logger.info("✓ Message persisted across node restart")

        node2.db_manager.close()

    @pytest.mark.asyncio
    async def test_database_stats(self, tmp_path):
        """Test database statistics reporting."""
        db_path = tmp_path / "test_stats.db"
        node = TADNode(db_path=str(db_path))

        # Add test messages
        for i in range(3):
            msg = {
                "msg_id": f"stats_test_{i}",
                "payload": {
                    "channel_id": "#general",
                    "type": "chat_message",
                    "content": f"Stats test {i}",
                    "timestamp": f"2025-11-04T12:{i:02d}:00",
                },
                "sender_id": "sender",
                "signature": f"sig_{i}",
            }
            node.db_manager.store_message(msg)

        stats = node.get_database_stats()
        assert stats["total_messages"] == 3
        assert stats["total_channels"] == 1
        assert "#general" in stats["messages_per_channel"]
        assert stats["messages_per_channel"]["#general"] == 3
        logger.info(f"✓ Database stats correct: {stats}")

        node.db_manager.close()


# Simple logger for tests
import logging

logger = logging.getLogger("test_milestone4")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("[%(name)-15s] %(levelname)-5s %(message)s")
)
logger.addHandler(handler)


# Test execution
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
