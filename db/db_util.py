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
CURRENT_SCHEMA_VERSION = 3


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
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
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


def _column_exists(conn: sqlite3.Connection, table_name: str, column_name: str) -> bool:
    """
    Check if a column exists in a table.
    
    Args:
        conn: Database connection.
        table_name: Name of the table to check.
        column_name: Name of the column to check.
        
    Returns:
        bool: True if the column exists, False otherwise.
    """
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def _apply_migration_v2(conn: sqlite3.Connection) -> None:
    """
    Apply schema version 2: Add JSON data columns to audit_summary and governance_analysis.
    
    This migration adds:
    - audit_data TEXT column to audit_summary (stores full audit_dict as JSON)
    - governance_data TEXT column to governance_analysis (stores full gov_dict as JSON)
    
    The migration is idempotent - columns are only added if they don't already exist.
    
    Args:
        conn: Database connection.
    """
    cursor = conn.cursor()
    
    # Add audit_data column to audit_summary if it doesn't exist
    if not _column_exists(conn, 'audit_summary', 'audit_data'):
        cursor.execute("""
            ALTER TABLE audit_summary
            ADD COLUMN audit_data TEXT
        """)
        logger.info("Added audit_data column to audit_summary table")
    else:
        logger.info("audit_data column already exists in audit_summary table")
    
    # Add governance_data column to governance_analysis if it doesn't exist
    if not _column_exists(conn, 'governance_analysis', 'governance_data'):
        cursor.execute("""
            ALTER TABLE governance_analysis
            ADD COLUMN governance_data TEXT
        """)
        logger.info("Added governance_data column to governance_analysis table")
    else:
        logger.info("governance_data column already exists in governance_analysis table")
    
    # Record migration
    cursor.execute("""
        INSERT INTO migrations (version, description)
        VALUES (?, ?)
    """, (2, "Add JSON data columns: audit_data to audit_summary, governance_data to governance_analysis"))
    
    conn.commit()
    logger.info("Applied migration v2: Added JSON data columns")


def _apply_migration_v3(conn: sqlite3.Connection) -> None:
    """
    Apply schema version 3: Normalize timestamps to ISO 8601 with microseconds.
    
    This migration converts all existing timestamps to strict ISO 8601 format with microseconds.
    Format: YYYY-MM-DDTHH:MM:SS.mmmmmm (e.g., 2025-11-18T10:30:00.123456)
    
    Tables affected:
    - pipeline_runs.timestamp
    - audit_summary.timestamp
    - migrations.applied_at
    
    The migration is idempotent and handles various input timestamp formats.
    
    Args:
        conn: Database connection.
    """
    from datetime import datetime
    
    cursor = conn.cursor()
    
    # Helper function to normalize timestamp strings
    def normalize_timestamp(ts_str: str) -> str:
        """Convert various timestamp formats to ISO 8601 with microseconds."""
        if not ts_str:
            return ts_str
        
        try:
            # Try parsing common formats
            formats_to_try = [
                '%Y-%m-%d %H:%M:%S.%f',      # 2025-11-18 10:30:00.123456
                '%Y-%m-%d %H:%M:%S',          # 2025-11-18 10:30:00
                '%Y-%m-%dT%H:%M:%S.%f',       # 2025-11-18T10:30:00.123456 (already correct)
                '%Y-%m-%dT%H:%M:%S',          # 2025-11-18T10:30:00
            ]
            
            dt = None
            for fmt in formats_to_try:
                try:
                    dt = datetime.strptime(ts_str, fmt)
                    break
                except ValueError:
                    continue
            
            if dt is None:
                logger.warning(f"Could not parse timestamp: {ts_str}")
                return ts_str
            
            # Convert to ISO 8601 with microseconds
            return dt.isoformat(timespec="microseconds")
            
        except Exception as e:
            logger.warning(f"Error normalizing timestamp '{ts_str}': {e}")
            return ts_str
    
    # Normalize pipeline_runs.timestamp
    cursor.execute("SELECT id, timestamp FROM pipeline_runs")
    pipeline_runs = cursor.fetchall()
    
    for row in pipeline_runs:
        run_id = row['id']
        old_timestamp = row['timestamp']
        new_timestamp = normalize_timestamp(old_timestamp)
        
        if new_timestamp != old_timestamp:
            cursor.execute("""
                UPDATE pipeline_runs
                SET timestamp = ?
                WHERE id = ?
            """, (new_timestamp, run_id))
            logger.info(f"Normalized pipeline_runs timestamp for id={run_id}: {old_timestamp} -> {new_timestamp}")
    
    # Normalize audit_summary.timestamp
    cursor.execute("SELECT id, timestamp FROM audit_summary WHERE timestamp IS NOT NULL")
    audit_summaries = cursor.fetchall()
    
    for row in audit_summaries:
        audit_id = row['id']
        old_timestamp = row['timestamp']
        new_timestamp = normalize_timestamp(old_timestamp)
        
        if new_timestamp != old_timestamp:
            cursor.execute("""
                UPDATE audit_summary
                SET timestamp = ?
                WHERE id = ?
            """, (new_timestamp, audit_id))
            logger.info(f"Normalized audit_summary timestamp for id={audit_id}: {old_timestamp} -> {new_timestamp}")
    
    # Normalize migrations.applied_at (for consistency)
    cursor.execute("SELECT version, applied_at FROM migrations")
    migrations = cursor.fetchall()
    
    for row in migrations:
        version = row['version']
        old_timestamp = row['applied_at']
        new_timestamp = normalize_timestamp(old_timestamp)
        
        if new_timestamp != old_timestamp:
            cursor.execute("""
                UPDATE migrations
                SET applied_at = ?
                WHERE version = ?
            """, (new_timestamp, version))
            logger.info(f"Normalized migrations timestamp for version={version}: {old_timestamp} -> {new_timestamp}")
    
    # Record migration
    cursor.execute("""
        INSERT INTO migrations (version, description)
        VALUES (?, ?)
    """, (3, "Normalize timestamps to ISO 8601 with microseconds"))
    
    conn.commit()
    logger.info("Applied migration v3: Normalized all timestamps to ISO 8601 with microseconds")


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
        2: _apply_migration_v2,
        3: _apply_migration_v3,
        # Future migrations can be added here:
        # 4: _apply_migration_v4,
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


# ============================================================================
# Write APIs
# ============================================================================

def insert_pipeline_run(timestamp: str, alerts_count: int, raw_data_path: Optional[str] = None) -> Optional[int]:
    """
    Insert a new pipeline run record.
    
    Args:
        timestamp: ISO format timestamp of the pipeline run.
        alerts_count: Number of alerts processed in this run.
        raw_data_path: Optional path to raw data file.
        
    Returns:
        int: The run_id of the inserted record, or None if insertion failed.
        
    Example:
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5, "data/samples/sample_logs.txt")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pipeline_runs (timestamp, alerts_count, raw_data_path)
                VALUES (?, ?, ?)
            """, (timestamp, alerts_count, raw_data_path))
            
            run_id = cursor.lastrowid
            logger.info(f"Inserted pipeline run {run_id} with {alerts_count} alerts at {timestamp}")
            return run_id
            
    except Exception as e:
        logger.error(f"Failed to insert pipeline run: {e}")
        return None


def insert_audit_summary(run_id: int, audit_dict: dict) -> bool:
    """
    Insert an audit summary record for a pipeline run.
    
    Args:
        run_id: The pipeline run ID to associate this audit with.
        audit_dict: Dictionary containing audit summary data. Can be either:
                   - Simple summary: {status, count, timestamp}
                   - Full audit entry: {execution_timestamp, total_incidents, stage_outputs, ...}
                   The full dictionary is stored as JSON in the audit_data column.
                   
    Returns:
        bool: True if insertion succeeded, False otherwise.
        
    Example:
        # Simple summary
        success = insert_audit_summary(
            run_id=1,
            audit_dict={
                "status": "completed",
                "count": 5,
                "timestamp": "2025-11-18T10:30:00"
            }
        )
        
        # Full audit entry
        success = insert_audit_summary(
            run_id=1,
            audit_dict={
                "execution_timestamp": "2025-11-18 10:30:00",
                "total_incidents": 5,
                "stage_outputs": {...},
                "resolution_plans": [...]
            }
        )
    """
    import json
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize the full audit_dict to JSON
            audit_data_json = json.dumps(audit_dict)
            
            # Extract fields - handle both simple summary and full audit entry formats
            # Use 'logged' as default only if we have a full audit entry (has execution_timestamp)
            if 'execution_timestamp' in audit_dict and 'status' not in audit_dict:
                status = 'logged'
            else:
                status = audit_dict.get('status')
            
            count = audit_dict.get('count') or audit_dict.get('total_incidents')
            timestamp = audit_dict.get('timestamp') or audit_dict.get('execution_timestamp')
            
            cursor.execute("""
                INSERT INTO audit_summary (run_id, status, count, timestamp, audit_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                status,
                count,
                timestamp,
                audit_data_json
            ))
            
            logger.info(f"Inserted audit summary for run_id {run_id}: status={status}, count={count}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to insert audit summary for run_id {run_id}: {e}")
        return False


def insert_governance_analysis(run_id: int, gov_dict: dict) -> bool:
    """
    Insert a governance analysis record for a pipeline run.
    
    Args:
        run_id: The pipeline run ID to associate this governance analysis with.
        gov_dict: Dictionary containing governance analysis data with keys:
                 - risk (str): Risk level or assessment
                 - escalation (str): Escalation decision or status
                 - commentary (str): Additional governance commentary
                 The full dictionary is also stored as JSON in the governance_data column.
                   
    Returns:
        bool: True if insertion succeeded, False otherwise.
        
    Example:
        success = insert_governance_analysis(
            run_id=1,
            gov_dict={
                "risk": "medium",
                "escalation": "required",
                "commentary": "Multiple compliance issues detected"
            }
        )
    """
    import json
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Serialize the full gov_dict to JSON
            governance_data_json = json.dumps(gov_dict)
            
            cursor.execute("""
                INSERT INTO governance_analysis (run_id, risk, escalation, commentary, governance_data)
                VALUES (?, ?, ?, ?, ?)
            """, (
                run_id,
                gov_dict.get('risk'),
                gov_dict.get('escalation'),
                gov_dict.get('commentary'),
                governance_data_json
            ))
            
            logger.info(f"Inserted governance analysis for run_id {run_id}: risk={gov_dict.get('risk')}, escalation={gov_dict.get('escalation')}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to insert governance analysis for run_id {run_id}: {e}")
        return False


def insert_compliance_issues(run_id: int, issues_list: list) -> bool:
    """
    Insert compliance issues for a pipeline run.
    
    Args:
        run_id: The pipeline run ID to associate these compliance issues with.
        issues_list: List of issue strings or dictionaries. If dictionaries are provided,
                    the 'issue' key will be extracted. If strings, they will be used directly.
                   
    Returns:
        bool: True if all insertions succeeded, False otherwise.
        
    Example:
        success = insert_compliance_issues(
            run_id=1,
            issues_list=[
                "Missing security patch for CVE-2024-1234",
                "Unauthorized access attempt detected",
                {"issue": "Configuration drift detected in production"}
            ]
        )
    """
    if not issues_list:
        logger.info(f"No compliance issues to insert for run_id {run_id}")
        return True
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Insert each issue
            for item in issues_list:
                # Handle both string and dict formats
                if isinstance(item, dict):
                    issue_text = item.get('issue', str(item))
                else:
                    issue_text = str(item)
                
                cursor.execute("""
                    INSERT INTO compliance_issues (run_id, issue)
                    VALUES (?, ?)
                """, (run_id, issue_text))
            
            logger.info(f"Inserted {len(issues_list)} compliance issue(s) for run_id {run_id}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to insert compliance issues for run_id {run_id}: {e}")
        return False


def insert_notification_event(run_id: int, channel: str, status: str, response: str) -> bool:
    """
    Insert a notification event record for a pipeline run.
    
    Args:
        run_id: The pipeline run ID to associate this notification event with.
        channel: The notification channel used (e.g., "email", "slack", "pushover").
        status: The status of the notification (e.g., "success", "failed", "pending").
        response: The response or result from the notification service.
                   
    Returns:
        bool: True if insertion succeeded, False otherwise.
        
    Example:
        success = insert_notification_event(
            run_id=1,
            channel="pushover",
            status="success",
            response='{"status": 1, "request": "abc123"}'
        )
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO notification_events (run_id, channel, status, response)
                VALUES (?, ?, ?, ?)
            """, (run_id, channel, status, response))
            
            logger.info(f"Inserted notification event for run_id {run_id}: channel={channel}, status={status}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to insert notification event for run_id {run_id}: {e}")
        return False


# ============================================================================
# Read APIs
# ============================================================================

def get_pipeline_runs(limit: Optional[int] = None) -> list[dict]:
    """
    Retrieve pipeline run records from the database.
    
    Args:
        limit: Optional maximum number of records to return. If None, returns all records.
               Records are ordered by timestamp descending (most recent first).
                   
    Returns:
        list[dict]: List of pipeline run records as dictionaries with keys:
                   - id (int): Pipeline run ID
                   - timestamp (str): ISO format timestamp
                   - alerts_count (int): Number of alerts processed
                   - raw_data_path (str): Path to raw data file (may be None)
                   Returns empty list if query fails or no records exist.
        
    Example:
        # Get all pipeline runs
        all_runs = get_pipeline_runs()
        
        # Get the 10 most recent runs
        recent_runs = get_pipeline_runs(limit=10)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional limit
            query = """
                SELECT id, timestamp, alerts_count, raw_data_path
                FROM pipeline_runs
                ORDER BY timestamp DESC
            """
            
            if limit is not None:
                query += f" LIMIT {int(limit)}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert Row objects to dictionaries
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'timestamp': row['timestamp'],
                    'alerts_count': row['alerts_count'],
                    'raw_data_path': row['raw_data_path']
                })
            
            logger.info(f"Retrieved {len(results)} pipeline run(s)" + (f" (limit={limit})" if limit else ""))
            return results
            
    except Exception as e:
        logger.error(f"Failed to retrieve pipeline runs: {e}")
        return []


def get_governance_history(limit: Optional[int] = None) -> list[dict]:
    """
    Retrieve governance analysis records with associated pipeline run information.
    
    Args:
        limit: Optional maximum number of records to return. If None, returns all records.
               Records are ordered by pipeline run timestamp descending (most recent first).
                   
    Returns:
        list[dict]: List of governance analysis records as dictionaries with keys:
                   - id (int): Governance analysis record ID
                   - run_id (int): Associated pipeline run ID
                   - timestamp (str): ISO format timestamp from pipeline run
                   - risk (str): Risk level or assessment (legacy column)
                   - escalation (str): Escalation decision or status (legacy column)
                   - commentary (str): Additional governance commentary (legacy column)
                   - governance_data (str): Full governance analysis as JSON string
                   Returns empty list if query fails or no records exist.
        
    Example:
        # Get all governance history
        all_governance = get_governance_history()
        
        # Get the 20 most recent governance analyses
        recent_governance = get_governance_history(limit=20)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with JOIN to get timestamp from pipeline_runs
            query = """
                SELECT 
                    g.id,
                    g.run_id,
                    p.timestamp,
                    g.risk,
                    g.escalation,
                    g.commentary,
                    g.governance_data
                FROM governance_analysis g
                JOIN pipeline_runs p ON g.run_id = p.id
                ORDER BY p.timestamp DESC
            """
            
            if limit is not None:
                query += f" LIMIT {int(limit)}"
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Convert Row objects to dictionaries
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'run_id': row['run_id'],
                    'timestamp': row['timestamp'],
                    'risk': row['risk'],
                    'escalation': row['escalation'],
                    'commentary': row['commentary'],
                    'governance_data': row['governance_data']
                })
            
            logger.info(f"Retrieved {len(results)} governance analysis record(s)" + (f" (limit={limit})" if limit else ""))
            return results
            
    except Exception as e:
        logger.error(f"Failed to retrieve governance history: {e}")
        return []


def get_notifications(run_id: Optional[int] = None) -> list[dict]:
    """
    Retrieve notification event records from the database.
    
    Args:
        run_id: Optional pipeline run ID to filter notifications. If None, returns all notifications.
                If provided, only returns notifications for that specific pipeline run.
                   
    Returns:
        list[dict]: List of notification event records as dictionaries with keys:
                   - id (int): Notification event ID
                   - run_id (int): Associated pipeline run ID
                   - channel (str): Notification channel (e.g., "email", "slack", "pushover")
                   - status (str): Notification status (e.g., "success", "failed", "pending")
                   - response (str): Response or result from the notification service
                   Returns empty list if query fails or no records exist.
        
    Example:
        # Get all notifications
        all_notifications = get_notifications()
        
        # Get notifications for a specific pipeline run
        run_notifications = get_notifications(run_id=1)
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Build query with optional run_id filter
            if run_id is not None:
                query = """
                    SELECT id, run_id, channel, status, response
                    FROM notification_events
                    WHERE run_id = ?
                    ORDER BY id DESC
                """
                cursor.execute(query, (run_id,))
            else:
                query = """
                    SELECT id, run_id, channel, status, response
                    FROM notification_events
                    ORDER BY id DESC
                """
                cursor.execute(query)
            
            rows = cursor.fetchall()
            
            # Convert Row objects to dictionaries
            results = []
            for row in rows:
                results.append({
                    'id': row['id'],
                    'run_id': row['run_id'],
                    'channel': row['channel'],
                    'status': row['status'],
                    'response': row['response']
                })
            
            filter_msg = f" for run_id {run_id}" if run_id is not None else ""
            logger.info(f"Retrieved {len(results)} notification event(s){filter_msg}")
            return results
            
    except Exception as e:
        logger.error(f"Failed to retrieve notifications: {e}")
        return []


def get_dashboard_metrics() -> dict:
    """
    Retrieve aggregated dashboard metrics from the database.
    
    This function computes summary statistics and aggregations across all pipeline runs,
    including total executions, total incidents, average incidents per run, and the
    timestamp of the most recent execution.
    
    Returns:
        dict: Dashboard metrics dictionary with keys:
             - total_executions (int): Total number of pipeline runs
             - total_incidents (int): Sum of all alerts across all runs
             - avg_incidents_per_run (float): Average number of incidents per run
             - last_execution_timestamp (str): ISO format timestamp of most recent run, or None if no runs
             Returns default values (zeros/None) if query fails or no data exists.
        
    Example:
        metrics = get_dashboard_metrics()
        print(f"Total executions: {metrics['total_executions']}")
        print(f"Total incidents: {metrics['total_incidents']}")
        print(f"Average incidents per run: {metrics['avg_incidents_per_run']:.1f}")
        print(f"Last execution: {metrics['last_execution_timestamp']}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get aggregated metrics
            query = """
                SELECT 
                    COUNT(*) as total_executions,
                    COALESCE(SUM(alerts_count), 0) as total_incidents,
                    COALESCE(AVG(alerts_count), 0.0) as avg_incidents_per_run,
                    MAX(timestamp) as last_execution_timestamp
                FROM pipeline_runs
            """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            # Build result dictionary
            result = {
                'total_executions': row['total_executions'] if row['total_executions'] else 0,
                'total_incidents': row['total_incidents'] if row['total_incidents'] else 0,
                'avg_incidents_per_run': float(row['avg_incidents_per_run']) if row['avg_incidents_per_run'] else 0.0,
                'last_execution_timestamp': row['last_execution_timestamp']
            }
            
            logger.info(f"Retrieved dashboard metrics: {result['total_executions']} executions, {result['total_incidents']} total incidents")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve dashboard metrics: {e}")
        # Return default values on error
        return {
            'total_executions': 0,
            'total_incidents': 0,
            'avg_incidents_per_run': 0.0,
            'last_execution_timestamp': None
        }


def get_compliance_stats() -> dict:
    """
    Retrieve aggregated compliance statistics from the database.
    
    This function computes summary statistics about compliance issues across all pipeline runs,
    including total issues, runs with issues, runs without issues, and average issues per run.
    
    Returns:
        dict: Compliance statistics dictionary with keys:
             - total_issues (int): Total number of compliance issues across all runs
             - runs_with_issues (int): Number of pipeline runs that have at least one compliance issue
             - runs_without_issues (int): Number of pipeline runs with no compliance issues
             - avg_issues_per_run (float): Average number of compliance issues per run (across all runs)
             Returns default values (zeros) if query fails or no data exists.
        
    Example:
        stats = get_compliance_stats()
        print(f"Total compliance issues: {stats['total_issues']}")
        print(f"Runs with issues: {stats['runs_with_issues']}")
        print(f"Runs without issues: {stats['runs_without_issues']}")
        print(f"Average issues per run: {stats['avg_issues_per_run']:.2f}")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get total issues and runs with issues
            query = """
                SELECT 
                    COUNT(*) as total_issues,
                    COUNT(DISTINCT run_id) as runs_with_issues
                FROM compliance_issues
            """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            total_issues = row['total_issues'] if row['total_issues'] else 0
            runs_with_issues = row['runs_with_issues'] if row['runs_with_issues'] else 0
            
            # Query to get total number of pipeline runs
            cursor.execute("SELECT COUNT(*) as total_runs FROM pipeline_runs")
            total_runs_row = cursor.fetchone()
            total_runs = total_runs_row['total_runs'] if total_runs_row['total_runs'] else 0
            
            # Calculate derived metrics
            runs_without_issues = max(0, total_runs - runs_with_issues)
            avg_issues_per_run = float(total_issues) / float(total_runs) if total_runs > 0 else 0.0
            
            # Build result dictionary
            result = {
                'total_issues': total_issues,
                'runs_with_issues': runs_with_issues,
                'runs_without_issues': runs_without_issues,
                'avg_issues_per_run': avg_issues_per_run
            }
            
            logger.info(f"Retrieved compliance stats: {total_issues} total issues across {runs_with_issues} runs")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve compliance stats: {e}")
        # Return default values on error
        return {
            'total_issues': 0,
            'runs_with_issues': 0,
            'runs_without_issues': 0,
            'avg_issues_per_run': 0.0
        }


def get_severity_distribution() -> dict[str, int]:
    """
    Retrieve aggregated severity distribution across all pipeline runs.
    
    This function extracts severity distribution data from the audit_data JSON column
    and aggregates it across all pipeline runs.
    
    Returns:
        dict: Dictionary mapping severity levels to total counts across all runs.
             Example: {'critical': 5, 'high': 12, 'medium': 8, 'low': 3}
             Returns empty dict if query fails or no data exists.
        
    Example:
        severity_dist = get_severity_distribution()
        for severity, count in severity_dist.items():
            print(f"{severity}: {count}")
    """
    import json
    from collections import defaultdict
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get all audit_data records
            query = """
                SELECT audit_data
                FROM audit_summary
                WHERE audit_data IS NOT NULL
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Aggregate severity data
            severity_totals = defaultdict(int)
            
            for row in rows:
                try:
                    audit_data = json.loads(row['audit_data'])
                    
                    # Extract severity distribution from stage_outputs
                    stage_outputs = audit_data.get('stage_outputs', {})
                    triage_stage = stage_outputs.get('triage_stage', {})
                    severity_dist = triage_stage.get('severity_distribution', {})
                    
                    # Aggregate counts
                    for severity, count in severity_dist.items():
                        severity_totals[severity] += count
                        
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse audit_data for severity distribution: {e}")
                    continue
            
            result = dict(severity_totals)
            logger.info(f"Retrieved severity distribution: {len(result)} severity levels")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve severity distribution: {e}")
        return {}


def get_category_distribution() -> dict[str, int]:
    """
    Retrieve aggregated category distribution across all pipeline runs.
    
    This function extracts category distribution data from the audit_data JSON column
    and aggregates it across all pipeline runs.
    
    Returns:
        dict: Dictionary mapping categories to total counts across all runs.
             Example: {'network': 10, 'security': 8, 'performance': 5}
             Returns empty dict if query fails or no data exists.
        
    Example:
        category_dist = get_category_distribution()
        for category, count in category_dist.items():
            print(f"{category}: {count}")
    """
    import json
    from collections import defaultdict
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get all audit_data records
            query = """
                SELECT audit_data
                FROM audit_summary
                WHERE audit_data IS NOT NULL
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Aggregate category data
            category_totals = defaultdict(int)
            
            for row in rows:
                try:
                    audit_data = json.loads(row['audit_data'])
                    
                    # Extract category distribution from stage_outputs
                    stage_outputs = audit_data.get('stage_outputs', {})
                    triage_stage = stage_outputs.get('triage_stage', {})
                    category_dist = triage_stage.get('category_distribution', {})
                    
                    # Aggregate counts
                    for category, count in category_dist.items():
                        category_totals[category] += count
                        
                except (json.JSONDecodeError, KeyError, TypeError) as e:
                    logger.warning(f"Failed to parse audit_data for category distribution: {e}")
                    continue
            
            result = dict(category_totals)
            logger.info(f"Retrieved category distribution: {len(result)} categories")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve category distribution: {e}")
        return {}


def get_timeline_data() -> list[dict]:
    """
    Retrieve timeline data for incident visualization.
    
    This function extracts execution timestamps and incident counts from pipeline runs
    to create timeline data for charting.
    
    Returns:
        list[dict]: List of timeline records with keys:
                   - timestamp (str): ISO format timestamp
                   - date (str): Date in YYYY-MM-DD format
                   - time (str): Time in HH:MM:SS format
                   - incidents (int): Number of incidents in that run
                   Returns empty list if query fails or no data exists.
        
    Example:
        timeline = get_timeline_data()
        for record in timeline:
            print(f"{record['date']} {record['time']}: {record['incidents']} incidents")
    """
    from datetime import datetime
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get pipeline runs ordered by timestamp
            query = """
                SELECT timestamp, alerts_count
                FROM pipeline_runs
                ORDER BY timestamp ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Build timeline data
            timeline = []
            
            for row in rows:
                timestamp_str = row['timestamp']
                alerts_count = row['alerts_count']
                
                try:
                    # Parse ISO 8601 timestamp with microseconds
                    # Format: 2025-11-18T10:30:00.123456
                    dt = datetime.fromisoformat(timestamp_str)
                    
                    timeline.append({
                        'timestamp': timestamp_str,
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M:%S'),
                        'incidents': alerts_count
                    })
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse timestamp '{timestamp_str}': {e}")
                    continue
            
            logger.info(f"Retrieved timeline data: {len(timeline)} records")
            return timeline
            
    except Exception as e:
        logger.error(f"Failed to retrieve timeline data: {e}")
        return []


def get_risk_trend() -> list[dict]:
    """
    Retrieve risk trend data across pipeline runs for historical analysis.
    
    This function extracts risk levels from governance analysis records and associates
    them with pipeline run timestamps to create a time-series of risk assessments.
    
    Returns:
        list[dict]: List of risk trend records ordered by timestamp (ascending) with keys:
                   - run_id (int): Pipeline run ID
                   - timestamp (str): ISO format timestamp from pipeline run
                   - risk (str): Risk level (low, medium, high, critical)
                   - date (str): Date in YYYY-MM-DD format
                   - time (str): Time in HH:MM:SS format
                   Returns empty list if query fails or no data exists.
        
    Example:
        risk_trend = get_risk_trend()
        for record in risk_trend:
            print(f"{record['date']} {record['time']}: Risk level {record['risk']}")
    """
    from datetime import datetime
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get risk levels with timestamps from pipeline runs
            query = """
                SELECT 
                    g.run_id,
                    p.timestamp,
                    g.risk
                FROM governance_analysis g
                JOIN pipeline_runs p ON g.run_id = p.id
                WHERE g.risk IS NOT NULL
                ORDER BY p.timestamp ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Build risk trend data
            risk_trend = []
            
            for row in rows:
                run_id = row['run_id']
                timestamp_str = row['timestamp']
                risk = row['risk']
                
                try:
                    # Parse ISO 8601 timestamp with microseconds
                    # Format: 2025-11-18T10:30:00.123456
                    dt = datetime.fromisoformat(timestamp_str)
                    
                    risk_trend.append({
                        'run_id': run_id,
                        'timestamp': timestamp_str,
                        'risk': risk,
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M:%S')
                    })
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse timestamp '{timestamp_str}' for run_id {run_id}: {e}")
                    continue
            
            logger.info(f"Retrieved risk trend data: {len(risk_trend)} records")
            return risk_trend
            
    except Exception as e:
        logger.error(f"Failed to retrieve risk trend: {e}")
        return []


def get_compliance_trend() -> list[dict]:
    """
    Retrieve compliance trend data across pipeline runs for historical analysis.
    
    This function counts the number of compliance issues per pipeline run and associates
    them with pipeline run timestamps to create a time-series of compliance issue counts.
    
    Returns:
        list[dict]: List of compliance trend records ordered by timestamp (ascending) with keys:
                   - run_id (int): Pipeline run ID
                   - timestamp (str): ISO format timestamp from pipeline run
                   - issue_count (int): Number of compliance issues in that run
                   - date (str): Date in YYYY-MM-DD format
                   - time (str): Time in HH:MM:SS format
                   Returns empty list if query fails or no data exists.
        
    Example:
        compliance_trend = get_compliance_trend()
        for record in compliance_trend:
            print(f"{record['date']} {record['time']}: {record['issue_count']} compliance issues")
    """
    from datetime import datetime
    
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get compliance issue counts per run with timestamps
            query = """
                SELECT 
                    p.id as run_id,
                    p.timestamp,
                    COALESCE(COUNT(c.id), 0) as issue_count
                FROM pipeline_runs p
                LEFT JOIN compliance_issues c ON p.id = c.run_id
                GROUP BY p.id, p.timestamp
                ORDER BY p.timestamp ASC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Build compliance trend data
            compliance_trend = []
            
            for row in rows:
                run_id = row['run_id']
                timestamp_str = row['timestamp']
                issue_count = row['issue_count']
                
                try:
                    # Parse ISO 8601 timestamp with microseconds
                    # Format: 2025-11-18T10:30:00.123456
                    dt = datetime.fromisoformat(timestamp_str)
                    
                    compliance_trend.append({
                        'run_id': run_id,
                        'timestamp': timestamp_str,
                        'issue_count': issue_count,
                        'date': dt.strftime('%Y-%m-%d'),
                        'time': dt.strftime('%H:%M:%S')
                    })
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Failed to parse timestamp '{timestamp_str}' for run_id {run_id}: {e}")
                    continue
            
            logger.info(f"Retrieved compliance trend data: {len(compliance_trend)} records")
            return compliance_trend
            
    except Exception as e:
        logger.error(f"Failed to retrieve compliance trend: {e}")
        return []


def get_escalation_text_counts() -> dict[str, int]:
    """
    Retrieve aggregated escalation text counts across all governance analyses.
    
    This function uses SQL GROUP BY to count occurrences of each unique escalation
    recommendation across all pipeline runs.
    
    Returns:
        dict: Dictionary mapping escalation text to occurrence counts.
             Example: {
                 'None required': 5,
                 'Monitor for recurring patterns': 3,
                 'Review with team lead if issues persist': 2,
                 'Escalate to on-call engineer': 1
             }
             Returns empty dict if query fails or no data exists.
        
    Example:
        escalation_counts = get_escalation_text_counts()
        for escalation_text, count in escalation_counts.items():
            print(f"{escalation_text}: {count} occurrences")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Use SQL GROUP BY to count escalation occurrences
            query = """
                SELECT escalation, COUNT(*) as count
                FROM governance_analysis
                WHERE escalation IS NOT NULL AND escalation != ''
                GROUP BY escalation
                ORDER BY count DESC
            """
            
            cursor.execute(query)
            rows = cursor.fetchall()
            
            # Build result dictionary
            result = {}
            for row in rows:
                result[row['escalation']] = row['count']
            
            logger.info(f"Retrieved escalation text counts: {len(result)} unique escalation types")
            return result
            
    except Exception as e:
        logger.error(f"Failed to retrieve escalation text counts: {e}")
        return {}


def get_recent_runs(limit: int = 10) -> list[dict]:
    """
    Retrieve recent pipeline run metadata for UI and InsightsAgent inputs.
    
    This function returns recent pipeline runs with their associated audit summaries
    and governance analyses, ordered by timestamp descending (most recent first).
    Uses pure SQL ordering + LIMIT for efficient retrieval.
    
    Args:
        limit: Maximum number of recent runs to return. Defaults to 10.
    
    Returns:
        list[dict]: List of recent pipeline run records with keys:
                   - run_id (int): Pipeline run ID
                   - timestamp (str): ISO format timestamp from pipeline run
                   - alerts_count (int): Number of alerts processed in this run
                   - raw_data_path (str): Path to raw data file (may be None)
                   - audit_data (str): Full audit summary as JSON string (may be None)
                   - governance_data (str): Full governance analysis as JSON string (may be None)
                   Returns empty list if query fails or no data exists.
        
    Example:
        # Get the 10 most recent runs
        recent = get_recent_runs()
        
        # Get the 5 most recent runs
        recent = get_recent_runs(limit=5)
        
        # Process recent runs for insights
        for run in recent:
            print(f"Run {run['run_id']} at {run['timestamp']}: {run['alerts_count']} alerts")
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            
            # Query to get recent pipeline runs with associated audit and governance data
            # Uses LEFT JOIN to include runs even if they don't have audit/governance data yet
            query = """
                SELECT 
                    p.id as run_id,
                    p.timestamp,
                    p.alerts_count,
                    p.raw_data_path,
                    a.audit_data,
                    g.governance_data
                FROM pipeline_runs p
                LEFT JOIN audit_summary a ON p.id = a.run_id
                LEFT JOIN governance_analysis g ON p.id = g.run_id
                ORDER BY p.timestamp DESC
                LIMIT ?
            """
            
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            
            # Build result list
            results = []
            for row in rows:
                results.append({
                    'run_id': row['run_id'],
                    'timestamp': row['timestamp'],
                    'alerts_count': row['alerts_count'],
                    'raw_data_path': row['raw_data_path'],
                    'audit_data': row['audit_data'],
                    'governance_data': row['governance_data']
                })
            
            logger.info(f"Retrieved {len(results)} recent pipeline run(s) (limit={limit})")
            return results
            
    except Exception as e:
        logger.error(f"Failed to retrieve recent runs: {e}")
        return []


# ============================================================================
# Database Initialization
# ============================================================================

# Initialize database on module import
try:
    initialize_database()
except Exception as e:
    logger.warning(f"Database initialization failed on import: {e}")
    logger.warning("Database operations will fail until initialization succeeds")
