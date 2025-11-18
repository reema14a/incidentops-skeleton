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
        audit_dict: Dictionary containing audit summary data with keys:
                   - status (str): Status of the audit
                   - count (int): Count of items audited
                   - timestamp (str): ISO format timestamp
                   
    Returns:
        bool: True if insertion succeeded, False otherwise.
        
    Example:
        success = insert_audit_summary(
            run_id=1,
            audit_dict={
                "status": "completed",
                "count": 5,
                "timestamp": "2025-11-18T10:30:00"
            }
        )
    """
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_summary (run_id, status, count, timestamp)
                VALUES (?, ?, ?, ?)
            """, (
                run_id,
                audit_dict.get('status'),
                audit_dict.get('count'),
                audit_dict.get('timestamp')
            ))
            
            logger.info(f"Inserted audit summary for run_id {run_id}: status={audit_dict.get('status')}, count={audit_dict.get('count')}")
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
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO governance_analysis (run_id, risk, escalation, commentary)
                VALUES (?, ?, ?, ?)
            """, (
                run_id,
                gov_dict.get('risk'),
                gov_dict.get('escalation'),
                gov_dict.get('commentary')
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
                   - risk (str): Risk level or assessment
                   - escalation (str): Escalation decision or status
                   - commentary (str): Additional governance commentary
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
                    g.commentary
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
                    'commentary': row['commentary']
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


# ============================================================================
# Database Initialization
# ============================================================================

# Initialize database on module import
try:
    initialize_database()
except Exception as e:
    logger.warning(f"Database initialization failed on import: {e}")
    logger.warning("Database operations will fail until initialization succeeds")
