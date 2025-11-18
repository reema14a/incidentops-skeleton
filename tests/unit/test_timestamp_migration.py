"""
Tests for timestamp normalization migration (v3).

This test verifies that the migration correctly converts old timestamp formats
to ISO 8601 with microseconds.
"""
import unittest
import sqlite3
import os
from datetime import datetime
from db.db_util import _apply_migration_v3


class TestTimestampMigration(unittest.TestCase):
    """Test timestamp normalization migration."""
    
    def setUp(self):
        """Set up test database with old format timestamps."""
        self.test_db = 'data/db/test_timestamp_migration.db'
        
        # Remove if exists
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        
        # Create connection and insert old format data
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Create tables manually (simulating old schema)
        cursor.execute('''
            CREATE TABLE migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE pipeline_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                alerts_count INTEGER NOT NULL DEFAULT 0,
                raw_data_path TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE audit_summary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                status TEXT,
                count INTEGER,
                timestamp TEXT,
                audit_data TEXT,
                FOREIGN KEY (run_id) REFERENCES pipeline_runs(id)
            )
        ''')
        
        # Insert old format timestamps (space-separated)
        cursor.execute('''
            INSERT INTO migrations (version, description, applied_at)
            VALUES (1, 'Initial schema', '2025-11-18 10:00:00')
        ''')
        
        cursor.execute('''
            INSERT INTO migrations (version, description, applied_at)
            VALUES (2, 'Add JSON columns', '2025-11-18 11:00:00')
        ''')
        
        cursor.execute('''
            INSERT INTO pipeline_runs (timestamp, alerts_count)
            VALUES ('2025-11-18 10:30:00', 5)
        ''')
        
        cursor.execute('''
            INSERT INTO pipeline_runs (timestamp, alerts_count)
            VALUES ('2025-11-18 11:45:00.123456', 3)
        ''')
        
        cursor.execute('''
            INSERT INTO audit_summary (run_id, status, count, timestamp)
            VALUES (1, 'logged', 5, '2025-11-18 10:30:00')
        ''')
        
        cursor.execute('''
            INSERT INTO audit_summary (run_id, status, count, timestamp)
            VALUES (2, 'logged', 3, '2025-11-18 11:45:00.123456')
        ''')
        
        conn.commit()
        conn.close()
    
    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
    
    def test_migration_normalizes_space_separated_timestamps(self):
        """Test that space-separated timestamps are converted to ISO 8601."""
        # Apply migration
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        _apply_migration_v3(conn)
        conn.close()
        
        # Check normalized format
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT timestamp FROM pipeline_runs WHERE id = 1')
        timestamp = cursor.fetchone()[0]
        
        # Should be ISO 8601 with T separator and microseconds
        self.assertIn('T', timestamp, "Timestamp should have T separator")
        self.assertIn('.', timestamp, "Timestamp should have microseconds")
        self.assertEqual(timestamp, '2025-11-18T10:30:00.000000')
        
        conn.close()
    
    def test_migration_preserves_microseconds(self):
        """Test that existing microseconds are preserved."""
        # Apply migration
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        _apply_migration_v3(conn)
        conn.close()
        
        # Check that microseconds are preserved
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT timestamp FROM pipeline_runs WHERE id = 2')
        timestamp = cursor.fetchone()[0]
        
        # Should preserve the microseconds
        self.assertIn('T', timestamp, "Timestamp should have T separator")
        self.assertIn('.123456', timestamp, "Timestamp should preserve microseconds")
        self.assertEqual(timestamp, '2025-11-18T11:45:00.123456')
        
        conn.close()
    
    def test_migration_normalizes_audit_summary_timestamps(self):
        """Test that audit_summary timestamps are normalized."""
        # Apply migration
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        _apply_migration_v3(conn)
        conn.close()
        
        # Check normalized format
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT timestamp FROM audit_summary WHERE id = 1')
        timestamp = cursor.fetchone()[0]
        
        # Should be ISO 8601 with T separator and microseconds
        self.assertIn('T', timestamp, "Timestamp should have T separator")
        self.assertIn('.', timestamp, "Timestamp should have microseconds")
        self.assertEqual(timestamp, '2025-11-18T10:30:00.000000')
        
        conn.close()
    
    def test_migration_normalizes_migrations_table(self):
        """Test that migrations table timestamps are normalized."""
        # Apply migration
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        _apply_migration_v3(conn)
        conn.close()
        
        # Check normalized format
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        
        cursor.execute('SELECT applied_at FROM migrations WHERE version = 1')
        timestamp = cursor.fetchone()[0]
        
        # Should be ISO 8601 with T separator and microseconds
        self.assertIn('T', timestamp, "Timestamp should have T separator")
        self.assertIn('.', timestamp, "Timestamp should have microseconds")
        
        conn.close()
    
    def test_migration_is_idempotent(self):
        """Test that running migration multiple times is safe."""
        # Apply migration twice
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        _apply_migration_v3(conn)
        conn.close()
        
        # Get timestamp after first migration
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp FROM pipeline_runs WHERE id = 1')
        timestamp1 = cursor.fetchone()[0]
        conn.close()
        
        # Apply migration again (should be idempotent)
        conn = sqlite3.connect(self.test_db)
        conn.row_factory = sqlite3.Row
        
        # Remove the migration record to allow re-running
        cursor = conn.cursor()
        cursor.execute('DELETE FROM migrations WHERE version = 3')
        conn.commit()
        
        _apply_migration_v3(conn)
        conn.close()
        
        # Get timestamp after second migration
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('SELECT timestamp FROM pipeline_runs WHERE id = 1')
        timestamp2 = cursor.fetchone()[0]
        conn.close()
        
        # Timestamps should be identical
        self.assertEqual(timestamp1, timestamp2, "Migration should be idempotent")


if __name__ == '__main__':
    unittest.main()
