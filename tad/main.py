"""
TAD Main Entry Point with Channel Support

This module provides the main entry point for starting a TAD node with channel support.

Usage:
    python -m tad.main
    or
    from tad.main import main; asyncio.run(main())

Channel Commands:
    /join #channel      - Join a channel
    /leave #channel     - Leave a channel
    /channels           - List subscribed channels
    #channel: message   - Send message to a specific channel
"""

import asyncio
import logging
import sys
from typing import Optional

from .node import TADNode

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)-20s] [%(levelname)-5s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)


class BasicTADApp:
    """
    A simple TAD application with channel support (Milestone 3).

    Demonstrates multi-channel messaging with local subscriptions.
    """

    def __init__(self):
        """Initialize the basic app."""
        self.node: Optional[TADNode] = None
        self.running = False
        self.current_channel: str = "#general"  # Default channel for input

    async def start(self) -> None:
        """Start the TAD node and begin operation."""
        # Create callbacks for the node
        def on_message(msg):
            """Handle received messages with channel awareness (Milestone 3)."""
            payload = msg.get("payload", {})
            msg_type = payload.get("type")
            content = payload.get("content", "")
            channel_id = payload.get("channel_id", "unknown")
            sender_id = msg.get("sender_id", "unknown")[:8]

            if msg_type == "chat_message":
                # Format: [#channel] <sender_id>: message
                print(f"\n[{channel_id}] <{sender_id}> {content}")
            elif msg_type == "HELLO":
                print(f"\n[{channel_id}] <{sender_id}> HELLO")

        def on_peer_discovered(peer_id, peer_addr):
            """Handle peer discovery."""
            print(f"\n[Peer] Discovered {peer_id[:8]} @ {peer_addr[0]}:{peer_addr[1]}")

        def on_peer_removed(peer_id):
            """Handle peer removal."""
            print(f"\n[Peer] Removed {peer_id[:8]}")

        # Create the TAD node with default channels
        self.node = TADNode(
            on_message_received=on_message,
            on_peer_discovered=on_peer_discovered,
            on_peer_removed=on_peer_removed,
        )

        # Start the node
        try:
            await self.node.start()
            self.running = True

            # Log initial channel subscriptions
            channels = self.node.get_subscribed_channels()
            logger.info(f"TAD node started. Subscribed to channels: {channels}")
            logger.info("Type messages and press Enter to broadcast.")
            logger.info("Commands: /join #channel | /leave #channel | /channels | #ch:message")
            logger.info("Press Ctrl+C to quit.")
        except Exception as e:
            logger.error(f"Failed to start TAD node: {e}", exc_info=True)
            raise

    async def stop(self) -> None:
        """Stop the TAD node gracefully."""
        if self.node:
            await self.node.stop()
        self.running = False

    async def handle_user_input(self) -> None:
        """Handle user input with channel command support (Milestone 3)."""
        loop = asyncio.get_event_loop()

        def read_input():
            """Read a line from stdin (blocking)."""
            try:
                return sys.stdin.readline().strip()
            except EOFError:
                return None

        while self.running:
            # Read input in a thread to avoid blocking the event loop
            user_input = await loop.run_in_executor(None, read_input)

            if user_input is None:
                # EOF
                break

            if user_input.lower() in ("quit", "exit"):
                break

            if user_input:
                # Handle channel commands (Milestone 3)
                if user_input.startswith("/join "):
                    # Command: /join #channelname
                    channel = user_input[6:].strip()
                    if channel.startswith("#"):
                        self.node.join_channel(channel)
                        logger.info(f"Joined channel: {channel}")
                    else:
                        logger.warning("Channel name must start with #")

                elif user_input.startswith("/leave "):
                    # Command: /leave #channelname
                    channel = user_input[7:].strip()
                    if channel.startswith("#"):
                        self.node.leave_channel(channel)
                        logger.info(f"Left channel: {channel}")
                    else:
                        logger.warning("Channel name must start with #")

                elif user_input == "/channels":
                    # Command: /channels - list subscribed channels
                    channels = self.node.get_subscribed_channels()
                    logger.info(f"Subscribed channels: {channels}")

                elif user_input.startswith("#") and ":" in user_input:
                    # Format: #channelname: message
                    parts = user_input.split(":", 1)
                    channel = parts[0].strip()
                    message = parts[1].strip()
                    if message and channel.startswith("#"):
                        msg_id = await self.node.broadcast_message(message, channel)
                        logger.info(f"Message sent to {channel} (ID: {msg_id})")

                else:
                    # Regular message to current channel
                    if self.node:
                        msg_id = await self.node.broadcast_message(user_input, self.current_channel)
                        logger.info(f"Message sent to {self.current_channel} (ID: {msg_id})")

            # Small delay to avoid busy-waiting
            await asyncio.sleep(0.01)

    async def run(self) -> None:
        """Run the TAD application."""
        try:
            await self.start()

            # Run until interrupted
            while self.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("\nShutdown signal received...")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            await self.stop()
            logger.info("Goodbye!")


async def main() -> None:
    """
    Main entry point for the TAD application.

    Creates a basic app instance and runs it.
    """
    app = BasicTADApp()
    await app.run()


if __name__ == "__main__":
    # Run the main async function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
