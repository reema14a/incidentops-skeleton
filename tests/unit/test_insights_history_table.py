"""
Unit tests for insights_history table migration and structure.
"""

import os
import sqlite3
import tempfile
import pytest
from pathlib import Path

from db.db_util import initialize_database, get_connection


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Set environment variable to use temp database
    original_db_path = os.environ.get('DB_PATH')
    os.environ['DB_PATH'] = db_path
    
    # Initialize database
    initialize_database()
    
    yield db_path
    
    # Cleanup
    if original_db_path:
        os.environ['DB_PATH'] = original_db_path
    else:
        os.environ.pop('DB_PATH', None)
    
    # Remove temp file
    if os.path.exists(db_path):
        os.remove(db_path)


def test_insights_history_table_exists(temp_db):
    """Test that insights_history table is created during initialization."""
    os.environ['DB_PATH'] = temp_db
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='insights_history'
        """)
        result = cursor.fetchone()
        
        assert result is not None, "insights_history table should exist"
        assert result['name'] == 'insights_history'


def test_insights_history_table_structure(temp_db):
    """Test that insights_history table has the correct structure."""
    os.environ['DB_PATH'] = temp_db
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(insights_history)")
        columns = cursor.fetchall()
        
        # Convert to dict for easier testing
        column_dict = {col['name']: col['type'] for col in columns}
        
        # Verify expected columns exist with correct types
        assert 'id' in column_dict, "id column should exist"
        assert column_dict['id'] == 'INTEGER', "id should be INTEGER"
        
        assert 'run_id' in column_dict, "run_id column should exist"
        assert column_dict['run_id'] == 'INTEGER', "run_id should be INTEGER"
        
        assert 'insights_data' in column_dict, "insights_data column should exist"
        assert column_dict['insights_data'] == 'TEXT', "insights_data should be TEXT"
        
        assert 'timestamp' in column_dict, "timestamp column should exist"
        assert column_dict['timestamp'] == 'TEXT', "timestamp should be TEXT"


def test_insights_history_foreign_key(temp_db):
    """Test that insights_history has a foreign key to pipeline_runs."""
    os.environ['DB_PATH'] = temp_db
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_key_list(insights_history)")
        foreign_keys = cursor.fetchall()
        
        # Should have one foreign key
        assert len(foreign_keys) > 0, "insights_history should have foreign key constraint"
        
        # Verify it references pipeline_runs
        fk = foreign_keys[0]
        assert fk['table'] == 'pipeline_runs', "Foreign key should reference pipeline_runs"
        assert fk['from'] == 'run_id', "Foreign key should be on run_id column"


def test_migration_v4_recorded(temp_db):
    """Test that migration v4 is recorded in migrations table."""
    os.environ['DB_PATH'] = temp_db
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT version, description FROM migrations WHERE version = 4")
        migration = cursor.fetchone()
        
        assert migration is not None, "Migration v4 should be recorded"
        assert migration['version'] == 4
        assert 'insights_history' in migration['description'].lower()


def test_migration_idempotency(temp_db):
    """Test that running migrations multiple times doesn't cause errors."""
    os.environ['DB_PATH'] = temp_db
    
    # Run initialization again
    initialize_database()
    
    # Verify migration v4 is still recorded only once
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM migrations WHERE version = 4")
        result = cursor.fetchone()
        
        assert result['count'] == 1, "Migration v4 should only be recorded once"


def test_insights_history_insert_and_query(temp_db):
    """Test basic insert and query operations on insights_history table."""
    os.environ['DB_PATH'] = temp_db
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # First, insert a pipeline run
        cursor.execute("""
            INSERT INTO pipeline_runs (timestamp, alerts_count)
            VALUES (?, ?)
        """, ('2025-11-19T10:00:00.000000', 5))
        run_id = cursor.lastrowid
        
        # Insert an insights record
        insights_json = '{"summary": "Test insights", "trends": ["trend1", "trend2"]}'
        timestamp = '2025-11-19T10:05:00.000000'
        
        cursor.execute("""
            INSERT INTO insights_history (run_id, insights_data, timestamp)
            VALUES (?, ?, ?)
        """, (run_id, insights_json, timestamp))
        
        # Query the record back
        cursor.execute("""
            SELECT run_id, insights_data, timestamp
            FROM insights_history
            WHERE run_id = ?
        """, (run_id,))
        
        result = cursor.fetchone()
        
        assert result is not None, "Should be able to query inserted record"
        assert result['run_id'] == run_id
        assert result['insights_data'] == insights_json
        assert result['timestamp'] == timestamp
