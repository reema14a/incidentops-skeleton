"""
Unit tests for database initialization and schema creation.
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from db.db_util import (
    initialize_database,
    get_connection,
    DatabaseError,
    _get_db_path,
    _create_migrations_table,
    _get_current_version,
    _apply_migration_v1,
    _run_migrations
)
from config.settings_loader import reset_settings


class TestDatabaseInitialization:
    """Test database initialization and schema creation."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
    
    def teardown_method(self):
        """Clean up after each test."""
        # Remove temporary database
        if os.path.exists(self.temp_db):
            os.remove(self.temp_db)
        
        # Remove temporary directory
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
        
        # Reset settings
        reset_settings()
    
    def test_database_file_creation(self):
        """Test that database file is created on initialization."""
        # Ensure database doesn't exist
        assert not os.path.exists(self.temp_db)
        
        # Initialize database
        initialize_database()
        
        # Verify database file was created
        assert os.path.exists(self.temp_db)
    
    def test_migrations_table_creation(self):
        """Test that migrations table is created."""
        initialize_database()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'")
            result = cursor.fetchone()
            
            assert result is not None
            assert result['name'] == 'migrations'
    
    def test_all_tables_created(self):
        """Test that all required tables are created."""
        initialize_database()
        
        expected_tables = [
            'pipeline_runs',
            'audit_summary',
            'governance_analysis',
            'compliance_issues',
            'notification_events',
            'insights_history',
            'migrations'
        ]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row['name'] for row in cursor.fetchall()]
            
            for table in expected_tables:
                assert table in tables, f"Table '{table}' not found in database"
    
    def test_pipeline_runs_schema(self):
        """Test pipeline_runs table schema."""
        initialize_database()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(pipeline_runs)")
            columns = {row['name']: row for row in cursor.fetchall()}
            
            # Verify columns exist
            assert 'id' in columns
            assert 'timestamp' in columns
            assert 'alerts_count' in columns
            assert 'raw_data_path' in columns
            
            # Verify column properties
            assert columns['id']['pk'] == 1  # Primary key
            assert columns['timestamp']['notnull'] == 1  # NOT NULL
            assert columns['alerts_count']['notnull'] == 1  # NOT NULL
    
    def test_foreign_key_constraints(self):
        """Test that foreign key constraints are properly defined."""
        initialize_database()
        
        tables_with_fks = [
            'audit_summary',
            'governance_analysis',
            'compliance_issues',
            'notification_events'
        ]
        
        with get_connection() as conn:
            cursor = conn.cursor()
            
            for table in tables_with_fks:
                cursor.execute(f"PRAGMA foreign_key_list({table})")
                fks = cursor.fetchall()
                
                # Each table should have at least one foreign key
                assert len(fks) > 0, f"Table '{table}' has no foreign keys"
                
                # Verify foreign key references pipeline_runs
                assert fks[0]['table'] == 'pipeline_runs'
                assert fks[0]['from'] == 'run_id'
    
    def test_migration_v1_applied(self):
        """Test that migration v1 is applied correctly."""
        initialize_database()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT version, description FROM migrations WHERE version = 1")
            migration = cursor.fetchone()
            
            assert migration is not None
            assert migration['version'] == 1
            assert 'Initial schema' in migration['description']
    
    def test_idempotent_initialization(self):
        """Test that calling initialize_database multiple times is safe."""
        # Initialize database multiple times
        initialize_database()
        initialize_database()
        initialize_database()
        
        # Verify migrations table has correct number of entries (v1, v2, v3, v4, v5, v6)
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM migrations")
            count = cursor.fetchone()['count']
            
            assert count == 6, f"Expected 6 migrations (v1, v2, v3, v4, v5, v6), found {count}"
    
    def test_connection_context_manager(self):
        """Test that connection context manager works correctly."""
        initialize_database()
        
        # Test successful connection
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_connection_rollback_on_error(self):
        """Test that connection rolls back on error."""
        initialize_database()
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                # This should fail (invalid SQL)
                cursor.execute("INVALID SQL")
        except DatabaseError:
            pass  # Expected
        
        # Database should still be accessible
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
    
    def test_row_factory_enabled(self):
        """Test that row factory is enabled for column access by name."""
        initialize_database()
        
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 as test_column")
            row = cursor.fetchone()
            
            # Should be able to access by column name
            assert row['test_column'] == 1
    
    def test_get_current_version(self):
        """Test getting current schema version."""
        initialize_database()
        
        with get_connection() as conn:
            version = _get_current_version(conn)
            assert version == 6  # Current schema version after v1, v2, v3, v4, v5, v6 migrations
    
    def test_database_path_from_settings(self):
        """Test that database path is correctly retrieved from settings."""
        from config.settings_loader import get_settings
        
        db_path = _get_db_path()
        assert db_path == self.temp_db
        
        # Also verify dot notation access works
        settings = get_settings()
        assert settings.database.path == self.temp_db


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
