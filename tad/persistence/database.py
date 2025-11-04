"""
TAD Database Persistence Layer (Milestone 4)

Provides SQLite-based persistent storage for:
- Channel metadata and subscriptions
- Message history with full content
- Message signatures and sender information
- Query interfaces for history retrieval

Architecture:
- Channels table: Registry of channels
- Messages table: Complete message history with signatures
- Parameterized queries: Prevention of SQL injection
- Duplicate prevention: INSERT OR IGNORE on msg_id
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages persistent storage of channels and messages using SQLite.

    Responsibilities:
    - Create and maintain database schema
    - Store messages (received and broadcast)
    - Retrieve message history for channels
    - Manage channel metadata
    - Handle duplicate message prevention
    """

    def __init__(self, db_path: str = "tad_node.db"):
        """
        Initialize the DatabaseManager and ensure database is ready.

        Args:
            db_path: Path to SQLite database file (created if doesn't exist)
        """
        self.db_path = Path(db_path)
        self.connection: Optional[sqlite3.Connection] = None

        # Connect to database
        self._connect()

        # Create tables if needed
        self._create_tables()

        logger.info(f"DatabaseManager initialized with database: {self.db_path}")

    def _connect(self) -> None:
        """
        Establish connection to SQLite database.

        Creates the database file if it doesn't exist.
        Sets row factory to return dictionaries instead of tuples.
        """
        try:
            self.connection = sqlite3.connect(str(self.db_path))
            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self.connection.row_factory = sqlite3.Row
            logger.debug(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise

    def _create_tables(self) -> None:
        """
        Create database schema if it doesn't exist.

        Tables:
        - channels: Channel metadata and subscription info
        - messages: Complete message history with signatures
        """
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()

            # Channels table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS channels (
                    channel_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    subscribed BOOLEAN DEFAULT 1
                )
            """)

            # Messages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    msg_id TEXT PRIMARY KEY,
                    channel_id TEXT NOT NULL,
                    sender_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    content TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(channel_id) REFERENCES channels(channel_id)
                )
            """)

            # Create indexes for efficient querying
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_channel_timestamp
                ON messages(channel_id, timestamp DESC)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_msg_id
                ON messages(msg_id)
            """)

            self.connection.commit()
            logger.debug("Database tables created/verified")

        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise

    def store_channel(self, channel_id: str, name: str = None) -> None:
        """
        Store or update a channel in the database.

        Args:
            channel_id: Channel identifier (e.g., "#general")
            name: Optional friendly name for the channel
        """
        if not self.connection:
            return

        try:
            cursor = self.connection.cursor()
            name = name or channel_id

            # INSERT OR REPLACE to handle updates
            cursor.execute(
                """
                INSERT OR REPLACE INTO channels (channel_id, name, created_at, subscribed)
                VALUES (?, ?, CURRENT_TIMESTAMP, 1)
                """,
                (channel_id, name),
            )

            self.connection.commit()
            logger.debug(f"Channel stored: {channel_id}")

        except sqlite3.Error as e:
            logger.error(f"Error storing channel {channel_id}: {e}")

    def get_all_channels(self) -> List[Dict[str, str]]:
        """
        Retrieve all channels from the database.

        Returns:
            List of dictionaries with channel_id and name
        """
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT channel_id, name FROM channels ORDER BY created_at")
            rows = cursor.fetchall()

            # Convert sqlite3.Row objects to dictionaries
            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            logger.error(f"Error retrieving channels: {e}")
            return []

    def store_message(self, message: Dict) -> bool:
        """
        Store a message in the database.

        Args:
            message: Message dictionary containing:
                - msg_id: Unique message identifier
                - payload: Message payload (contains channel_id, type, content, timestamp)
                - sender_id: Public key of sender
                - signature: Message signature
                - ttl: Time-to-live (optional)

        Returns:
            True if stored successfully, False if duplicate or error
        """
        if not self.connection:
            return False

        try:
            payload = message.get("payload", {})
            channel_id = payload.get("channel_id", "#general")
            content = payload.get("content", "")
            timestamp = payload.get("timestamp", "")
            msg_id = message.get("msg_id", "")
            sender_id = message.get("sender_id", "")
            signature = message.get("signature", "")

            # Store channel if not exists
            self.store_channel(channel_id)

            cursor = self.connection.cursor()

            # INSERT OR IGNORE prevents duplicates on msg_id
            cursor.execute(
                """
                INSERT OR IGNORE INTO messages
                (msg_id, channel_id, sender_id, timestamp, content, signature)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (msg_id, channel_id, sender_id, timestamp, content, signature),
            )

            self.connection.commit()

            if cursor.rowcount > 0:
                logger.debug(f"Message stored: {msg_id} in {channel_id}")
                return True
            else:
                logger.debug(f"Message ignored (duplicate): {msg_id}")
                return False

        except sqlite3.Error as e:
            logger.error(f"Error storing message: {e}")
            return False

    def get_messages_for_channel(
        self, channel_id: str, last_n: int = 50
    ) -> List[Dict]:
        """
        Retrieve message history for a specific channel.

        Args:
            channel_id: Channel to retrieve messages from
            last_n: Maximum number of messages to retrieve (default: 50)

        Returns:
            List of message dictionaries, ordered by timestamp (oldest first)
        """
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()

            # Parameterized query to prevent SQL injection
            cursor.execute(
                """
                SELECT
                    msg_id,
                    channel_id,
                    sender_id,
                    timestamp,
                    content,
                    signature
                FROM messages
                WHERE channel_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (channel_id, last_n),
            )

            rows = cursor.fetchall()

            # Convert to dictionaries and reverse to get oldest first
            messages = [dict(row) for row in rows]
            messages.reverse()

            logger.debug(f"Retrieved {len(messages)} messages for {channel_id}")
            return messages

        except sqlite3.Error as e:
            logger.error(f"Error retrieving messages for {channel_id}: {e}")
            return []

    def get_message_count(self, channel_id: str = None) -> int:
        """
        Get total count of messages in database or for a specific channel.

        Args:
            channel_id: Optional channel_id to count messages for

        Returns:
            Total message count
        """
        if not self.connection:
            return 0

        try:
            cursor = self.connection.cursor()

            if channel_id:
                cursor.execute(
                    "SELECT COUNT(*) as count FROM messages WHERE channel_id = ?",
                    (channel_id,),
                )
            else:
                cursor.execute("SELECT COUNT(*) as count FROM messages")

            result = cursor.fetchone()
            return result["count"] if result else 0

        except sqlite3.Error as e:
            logger.error(f"Error counting messages: {e}")
            return 0

    def delete_old_messages(self, channel_id: str = None, days: int = 30) -> int:
        """
        Delete messages older than specified number of days.

        Args:
            channel_id: Optional channel to clean. If None, cleans all channels
            days: Delete messages older than this many days

        Returns:
            Number of messages deleted
        """
        if not self.connection:
            return 0

        try:
            cursor = self.connection.cursor()

            if channel_id:
                cursor.execute(
                    """
                    DELETE FROM messages
                    WHERE channel_id = ?
                    AND datetime(timestamp) < datetime('now', ? || ' days')
                    """,
                    (channel_id, -days),
                )
            else:
                cursor.execute(
                    """
                    DELETE FROM messages
                    WHERE datetime(timestamp) < datetime('now', ? || ' days')
                    """,
                    (-days,),
                )

            self.connection.commit()
            deleted_count = cursor.rowcount

            logger.info(f"Deleted {deleted_count} old messages")
            return deleted_count

        except sqlite3.Error as e:
            logger.error(f"Error deleting old messages: {e}")
            return 0

    def search_messages(
        self, channel_id: str, query: str, limit: int = 50
    ) -> List[Dict]:
        """
        Search for messages in a channel by content (simple text search).

        Args:
            channel_id: Channel to search in
            query: Search text
            limit: Maximum results to return

        Returns:
            List of matching message dictionaries
        """
        if not self.connection:
            return []

        try:
            cursor = self.connection.cursor()

            # Simple LIKE search (case-insensitive)
            cursor.execute(
                """
                SELECT
                    msg_id,
                    channel_id,
                    sender_id,
                    timestamp,
                    content,
                    signature
                FROM messages
                WHERE channel_id = ?
                AND content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (channel_id, f"%{query}%", limit),
            )

            rows = cursor.fetchall()
            messages = [dict(row) for row in rows]
            messages.reverse()

            logger.debug(f"Found {len(messages)} messages matching '{query}' in {channel_id}")
            return messages

        except sqlite3.Error as e:
            logger.error(f"Error searching messages: {e}")
            return []

    def close(self) -> None:
        """Close database connection gracefully."""
        if self.connection:
            try:
                self.connection.close()
                logger.debug("Database connection closed")
            except sqlite3.Error as e:
                logger.error(f"Error closing database: {e}")

    def __del__(self):
        """Cleanup: Close connection on object deletion."""
        self.close()

    def get_database_stats(self) -> Dict[str, int]:
        """
        Get database statistics for monitoring.

        Returns:
            Dictionary with counts of channels and messages
        """
        stats = {
            "total_messages": self.get_message_count(),
            "total_channels": len(self.get_all_channels()),
        }

        if self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute(
                    """
                    SELECT channel_id, COUNT(*) as count
                    FROM messages
                    GROUP BY channel_id
                    """
                )
                rows = cursor.fetchall()
                stats["messages_per_channel"] = {row["channel_id"]: row["count"] for row in rows}
            except sqlite3.Error as e:
                logger.warning(f"Could not get per-channel stats: {e}")

        return stats
