"""
TAD Persistence Layer

This module provides persistent storage capabilities for the TAD network.

Components:
- DatabaseManager: SQLite-based message storage and retrieval
"""

from .database import DatabaseManager

__all__ = ["DatabaseManager"]
