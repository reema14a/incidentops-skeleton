"""
Database utility module for IncidentOps SQLite storage.

This module provides the single point of access for all database operations.
No other module should contain SQL or direct database access.
"""

import sqlite3
import logging
from contextlib import contextmanager
from typing import Optional
from pathlib import Path

from config.settings_loader import get_settings


logger = logging.getLogger(__name__)


# Schema version for migration tracking
CURRENT_SCHEMA_VERSION = 1


class DatabaseError(Exception):
    """Custom exception for database-related errors."""
    pass


def _get_db_path() -> str:
    """
    Get the database path from settings.
    
    Returns:
        str: Path to the SQLite database file.
    """
    settings = get_settings()
    
    # Use dot notation to access database.path
    if 'database' not in settings or 'path' not in settings.database:
        raise DatabaseError("Database path not configured in settings")
    
    db_path = settings.database.path
    
    if not db_path:
        raise DatabaseError("Database path not configured in settings")
    
    return db_path


@contextmanager
def get_connection():
    """
    Context manager for database connections.
    
    Provides a connection with automatic commit/rollback and cleanup.
    
    Yields:
        sqlite3.Connection: Database connection.
        
    Example:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs")
    """
    db_path = _get_db_path()
    conn = None
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Database error: {e}")
        raise DatabaseError(f"Database operation failed: {e}")
    finally:
        if conn:
            conn.close()


def _create_migrations_table(conn: sqlite3.Connection) -> None:
    """
    Create the migrations tracking table if it doesn't exist.
    
    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            description TEXT
        )
    """)
    conn.commit()


def _get_current_version(conn: sqlite3.Connection) -> int:
    """
    Get the current schema version from the migrations table.
    
    Args:
        conn: Database connection.
        
    Returns:
        int: Current schema version, or 0 if no migrations applied.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(version) as version FROM migrations")
    row = cursor.fetchone()
    return row['version'] if row['version'] is not None else 0


def _apply_migration_v1(conn: sqlite3.Connection) -> None:
    """
    Apply schema version 1: Create initial tables.
    
    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    
    # Table 1: pipeline_runs
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            alerts_count INTEGER NOT NULL DEFAULT 0,
            raw_data_path TEXT
        )
    """)
    
    # Table 2: audit_summary
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            status TEXT,
            count INTEGER,
            timestamp TEXT,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
        )
    """)
    
    # Table 3: governance_analysis
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS governance_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            risk TEXT,
            escalation TEXT,
            commentary TEXT,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
        )
    """)
    
    # Table 4: compliance_issues
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS compliance_issues (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            issue TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
        )
    """)
    
    # Table 5: notification_events
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            status TEXT NOT NULL,
            response TEXT,
            FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
        )
    """)
    
    # Record migration
    cursor.execute("""
        INSERT INTO migrations (version, description)
        VALUES (?, ?)
    """, (1, "Initial schema: pipeline_runs, audit_summary, governance_analysis, compliance_issues, notification_events"))
    
    conn.commit()
    logger.info("Applied migration v1: Initial schema created")


def _run_migrations(conn: sqlite3.Connection) -> None:
    """
    Run all pending migrations in order.
    
    Args:
        conn: Database connection.
    """
    current_version = _get_current_version(conn)
    
    # Define migrations in order
    migrations = {
        1: _apply_migration_v1,
        # Future migrations can be added here:
        # 2: _apply_migration_v2,
        # 3: _apply_migration_v3,
    }
    
    # Apply pending migrations
    for version in sorted(migrations.keys()):
        if version > current_version:
            logger.info(f"Applying migration v{version}...")
            migrations[version](conn)


def initialize_database() -> None:
    """
    Initialize the database and apply all migrations.
    
    This function:
    1. Creates the database file if it doesn't exist
    2. Creates the migrations tracking table
    3. Applies all pending schema migrations
    
    This is idempotent and safe to call multiple times.
    """
    db_path = _get_db_path()
    
    # Ensure the data directory exists
    db_dir = Path(db_path).parent
    db_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing database at {db_path}")
    
    try:
        with get_connection() as conn:
            # Create migrations table
            _create_migrations_table(conn)
            
            # Run migrations
            _run_migrations(conn)
            
        logger.info("Database initialization complete")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(f"Database initialization failed: {e}")


# Initialize database on module import
try:
    initialize_database()
except Exception as e:
    logger.warning(f"Database initialization failed on import: {e}")
    logger.warning("Database operations will fail until initialization succeeds")
