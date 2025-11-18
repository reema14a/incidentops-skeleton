"""
Unit tests for database write APIs.
"""

import os
import sys
import tempfile
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from db.db_util import (
    initialize_database,
    get_connection,
    insert_pipeline_run,
    insert_audit_summary,
    insert_governance_analysis,
    insert_compliance_issues,
    insert_notification_event
)
from config.settings_loader import reset_settings


class TestInsertPipelineRun:
    """Test insert_pipeline_run write API."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
        
        # Initialize database
        initialize_database()
    
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
    
    def test_insert_pipeline_run_basic(self):
        """Test basic pipeline run insertion."""
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 5
        
        run_id = insert_pipeline_run(timestamp, alerts_count)
        
        # Verify run_id is returned
        assert run_id is not None
        assert isinstance(run_id, int)
        assert run_id > 0
    
    def test_insert_pipeline_run_with_raw_data_path(self):
        """Test pipeline run insertion with raw_data_path."""
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 3
        raw_data_path = "data/samples/sample_logs.txt"
        
        run_id = insert_pipeline_run(timestamp, alerts_count, raw_data_path)
        
        # Verify insertion
        assert run_id is not None
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['timestamp'] == timestamp
            assert row['alerts_count'] == alerts_count
            assert row['raw_data_path'] == raw_data_path
    
    def test_insert_pipeline_run_without_raw_data_path(self):
        """Test pipeline run insertion without raw_data_path."""
        timestamp = "2025-11-18T11:00:00"
        alerts_count = 10
        
        run_id = insert_pipeline_run(timestamp, alerts_count)
        
        # Verify insertion
        assert run_id is not None
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['timestamp'] == timestamp
            assert row['alerts_count'] == alerts_count
            assert row['raw_data_path'] is None
    
    def test_insert_multiple_pipeline_runs(self):
        """Test inserting multiple pipeline runs."""
        runs = [
            ("2025-11-18T10:00:00", 5, "data/samples/log1.txt"),
            ("2025-11-18T11:00:00", 3, None),
            ("2025-11-18T12:00:00", 8, "data/samples/log2.txt"),
        ]
        
        run_ids = []
        for timestamp, alerts_count, raw_data_path in runs:
            run_id = insert_pipeline_run(timestamp, alerts_count, raw_data_path)
            assert run_id is not None
            run_ids.append(run_id)
        
        # Verify all runs are unique
        assert len(run_ids) == len(set(run_ids))
        
        # Verify all runs are in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM pipeline_runs")
            count = cursor.fetchone()['count']
            assert count == len(runs)
    
    def test_insert_pipeline_run_with_zero_alerts(self):
        """Test pipeline run insertion with zero alerts."""
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 0
        
        run_id = insert_pipeline_run(timestamp, alerts_count)
        
        # Verify insertion
        assert run_id is not None
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['alerts_count'] == 0
    
    def test_insert_pipeline_run_autoincrement(self):
        """Test that run_id auto-increments correctly."""
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Verify auto-increment
        assert run_id_2 == run_id_1 + 1
        assert run_id_3 == run_id_2 + 1
    
    def test_insert_pipeline_run_transaction_commit(self):
        """Test that insert commits transaction correctly."""
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 5
        
        run_id = insert_pipeline_run(timestamp, alerts_count)
        
        # Open a new connection to verify commit
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pipeline_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['id'] == run_id


class TestInsertAuditSummary:
    """Test insert_audit_summary write API."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
        
        # Initialize database
        initialize_database()
        
        # Create a test pipeline run
        self.run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
    
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
    
    def test_insert_audit_summary_basic(self):
        """Test basic audit summary insertion."""
        audit_dict = {
            "status": "completed",
            "count": 5,
            "timestamp": "2025-11-18T10:30:00"
        }
        
        success = insert_audit_summary(self.run_id, audit_dict)
        
        # Verify success
        assert success is True
    
    def test_insert_audit_summary_data_verification(self):
        """Test audit summary data is correctly stored."""
        audit_dict = {
            "status": "completed",
            "count": 5,
            "timestamp": "2025-11-18T10:30:00"
        }
        
        success = insert_audit_summary(self.run_id, audit_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_summary WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
            assert row['status'] == "completed"
            assert row['count'] == 5
            assert row['timestamp'] == "2025-11-18T10:30:00"
    
    def test_insert_audit_summary_with_partial_data(self):
        """Test audit summary insertion with partial data."""
        audit_dict = {
            "status": "in_progress",
            "count": 3
            # timestamp is missing
        }
        
        success = insert_audit_summary(self.run_id, audit_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_summary WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['status'] == "in_progress"
            assert row['count'] == 3
            assert row['timestamp'] is None
    
    def test_insert_audit_summary_with_empty_dict(self):
        """Test audit summary insertion with empty dictionary."""
        audit_dict = {}
        
        success = insert_audit_summary(self.run_id, audit_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_summary WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
            assert row['status'] is None
            assert row['count'] is None
            assert row['timestamp'] is None
    
    def test_insert_multiple_audit_summaries(self):
        """Test inserting multiple audit summaries for different runs."""
        # Create additional pipeline runs
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Insert audit summaries
        audit_1 = {"status": "completed", "count": 5, "timestamp": "2025-11-18T10:30:00"}
        audit_2 = {"status": "failed", "count": 3, "timestamp": "2025-11-18T11:30:00"}
        audit_3 = {"status": "completed", "count": 8, "timestamp": "2025-11-18T12:30:00"}
        
        success_1 = insert_audit_summary(self.run_id, audit_1)
        success_2 = insert_audit_summary(run_id_2, audit_2)
        success_3 = insert_audit_summary(run_id_3, audit_3)
        
        assert success_1 is True
        assert success_2 is True
        assert success_3 is True
        
        # Verify all summaries are in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM audit_summary")
            count = cursor.fetchone()['count']
            assert count == 3
    
    def test_insert_audit_summary_with_invalid_run_id(self):
        """Test audit summary insertion with non-existent run_id."""
        invalid_run_id = 99999
        audit_dict = {
            "status": "completed",
            "count": 5,
            "timestamp": "2025-11-18T10:30:00"
        }
        
        # This should fail due to foreign key constraint
        success = insert_audit_summary(invalid_run_id, audit_dict)
        assert success is False
    
    def test_insert_audit_summary_transaction_commit(self):
        """Test that insert commits transaction correctly."""
        audit_dict = {
            "status": "completed",
            "count": 5,
            "timestamp": "2025-11-18T10:30:00"
        }
        
        success = insert_audit_summary(self.run_id, audit_dict)
        assert success is True
        
        # Open a new connection to verify commit
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_summary WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])


class TestInsertGovernanceAnalysis:
    """Test insert_governance_analysis write API."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
        
        # Initialize database
        initialize_database()
        
        # Create a test pipeline run
        self.run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
    
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
    
    def test_insert_governance_analysis_basic(self):
        """Test basic governance analysis insertion."""
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": "Multiple compliance issues detected"
        }
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        
        # Verify success
        assert success is True
    
    def test_insert_governance_analysis_data_verification(self):
        """Test governance analysis data is correctly stored."""
        gov_dict = {
            "risk": "high",
            "escalation": "immediate",
            "commentary": "Critical security vulnerability detected"
        }
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM governance_analysis WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
            assert row['risk'] == "high"
            assert row['escalation'] == "immediate"
            assert row['commentary'] == "Critical security vulnerability detected"
    
    def test_insert_governance_analysis_with_partial_data(self):
        """Test governance analysis insertion with partial data."""
        gov_dict = {
            "risk": "low",
            "escalation": "none"
            # commentary is missing
        }
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM governance_analysis WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['risk'] == "low"
            assert row['escalation'] == "none"
            assert row['commentary'] is None
    
    def test_insert_governance_analysis_with_empty_dict(self):
        """Test governance analysis insertion with empty dictionary."""
        gov_dict = {}
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM governance_analysis WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
            assert row['risk'] is None
            assert row['escalation'] is None
            assert row['commentary'] is None
    
    def test_insert_multiple_governance_analyses(self):
        """Test inserting multiple governance analyses for different runs."""
        # Create additional pipeline runs
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Insert governance analyses
        gov_1 = {"risk": "low", "escalation": "none", "commentary": "All systems normal"}
        gov_2 = {"risk": "medium", "escalation": "monitor", "commentary": "Minor issues detected"}
        gov_3 = {"risk": "high", "escalation": "immediate", "commentary": "Critical issues found"}
        
        success_1 = insert_governance_analysis(self.run_id, gov_1)
        success_2 = insert_governance_analysis(run_id_2, gov_2)
        success_3 = insert_governance_analysis(run_id_3, gov_3)
        
        assert success_1 is True
        assert success_2 is True
        assert success_3 is True
        
        # Verify all analyses are in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM governance_analysis")
            count = cursor.fetchone()['count']
            assert count == 3
    
    def test_insert_governance_analysis_with_invalid_run_id(self):
        """Test governance analysis insertion with non-existent run_id."""
        invalid_run_id = 99999
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": "Test commentary"
        }
        
        # This should fail due to foreign key constraint
        success = insert_governance_analysis(invalid_run_id, gov_dict)
        assert success is False
    
    def test_insert_governance_analysis_transaction_commit(self):
        """Test that insert commits transaction correctly."""
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": "Multiple compliance issues detected"
        }
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        assert success is True
        
        # Open a new connection to verify commit
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM governance_analysis WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
    
    def test_insert_governance_analysis_with_long_commentary(self):
        """Test governance analysis insertion with long commentary text."""
        long_commentary = "This is a very long commentary. " * 100
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": long_commentary
        }
        
        success = insert_governance_analysis(self.run_id, gov_dict)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM governance_analysis WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['commentary'] == long_commentary


class TestInsertComplianceIssues:
    """Test insert_compliance_issues write API."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
        
        # Initialize database
        initialize_database()
        
        # Create a test pipeline run
        self.run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
    
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
    
    def test_insert_compliance_issues_with_strings(self):
        """Test inserting compliance issues as strings."""
        issues_list = [
            "Missing security patch for CVE-2024-1234",
            "Unauthorized access attempt detected",
            "Configuration drift detected in production"
        ]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        
        # Verify success
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            count = cursor.fetchone()['count']
            assert count == 3
    
    def test_insert_compliance_issues_with_dicts(self):
        """Test inserting compliance issues as dictionaries."""
        issues_list = [
            {"issue": "Database backup failed"},
            {"issue": "SSL certificate expiring soon"},
            {"issue": "Disk space low on server"}
        ]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        
        # Verify success
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT issue FROM compliance_issues WHERE run_id = ? ORDER BY id", (self.run_id,))
            rows = cursor.fetchall()
            
            assert len(rows) == 3
            assert rows[0]['issue'] == "Database backup failed"
            assert rows[1]['issue'] == "SSL certificate expiring soon"
            assert rows[2]['issue'] == "Disk space low on server"
    
    def test_insert_compliance_issues_mixed_format(self):
        """Test inserting compliance issues with mixed string and dict format."""
        issues_list = [
            "String issue 1",
            {"issue": "Dict issue 1"},
            "String issue 2",
            {"issue": "Dict issue 2"}
        ]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        
        # Verify success
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT issue FROM compliance_issues WHERE run_id = ? ORDER BY id", (self.run_id,))
            rows = cursor.fetchall()
            
            assert len(rows) == 4
            assert rows[0]['issue'] == "String issue 1"
            assert rows[1]['issue'] == "Dict issue 1"
            assert rows[2]['issue'] == "String issue 2"
            assert rows[3]['issue'] == "Dict issue 2"
    
    def test_insert_compliance_issues_empty_list(self):
        """Test inserting empty compliance issues list."""
        issues_list = []
        
        success = insert_compliance_issues(self.run_id, issues_list)
        
        # Verify success (should succeed with no insertions)
        assert success is True
        
        # Verify no data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            count = cursor.fetchone()['count']
            assert count == 0
    
    def test_insert_compliance_issues_single_issue(self):
        """Test inserting a single compliance issue."""
        issues_list = ["Single compliance issue"]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        
        # Verify success
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT issue FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['issue'] == "Single compliance issue"
    
    def test_insert_compliance_issues_multiple_runs(self):
        """Test inserting compliance issues for multiple runs."""
        # Create additional pipeline runs
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Insert compliance issues for each run
        issues_1 = ["Issue 1 for run 1", "Issue 2 for run 1"]
        issues_2 = ["Issue 1 for run 2"]
        issues_3 = ["Issue 1 for run 3", "Issue 2 for run 3", "Issue 3 for run 3"]
        
        success_1 = insert_compliance_issues(self.run_id, issues_1)
        success_2 = insert_compliance_issues(run_id_2, issues_2)
        success_3 = insert_compliance_issues(run_id_3, issues_3)
        
        assert success_1 is True
        assert success_2 is True
        assert success_3 is True
        
        # Verify counts for each run
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            assert cursor.fetchone()['count'] == 2
            
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (run_id_2,))
            assert cursor.fetchone()['count'] == 1
            
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (run_id_3,))
            assert cursor.fetchone()['count'] == 3
    
    def test_insert_compliance_issues_with_invalid_run_id(self):
        """Test compliance issues insertion with non-existent run_id."""
        invalid_run_id = 99999
        issues_list = ["Test issue"]
        
        # This should fail due to foreign key constraint
        success = insert_compliance_issues(invalid_run_id, issues_list)
        assert success is False
    
    def test_insert_compliance_issues_transaction_commit(self):
        """Test that insert commits transaction correctly."""
        issues_list = ["Issue 1", "Issue 2"]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        assert success is True
        
        # Open a new connection to verify commit
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            count = cursor.fetchone()['count']
            
            assert count == 2
    
    def test_insert_compliance_issues_with_long_text(self):
        """Test inserting compliance issues with long text."""
        long_issue = "This is a very long compliance issue description. " * 50
        issues_list = [long_issue]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT issue FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['issue'] == long_issue
    
    def test_insert_compliance_issues_with_special_characters(self):
        """Test inserting compliance issues with special characters."""
        issues_list = [
            "Issue with 'single quotes'",
            'Issue with "double quotes"',
            "Issue with \n newlines \n and \t tabs",
            "Issue with unicode: 你好世界 🚀"
        ]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT issue FROM compliance_issues WHERE run_id = ? ORDER BY id", (self.run_id,))
            rows = cursor.fetchall()
            
            assert len(rows) == 4
            for i, row in enumerate(rows):
                assert row['issue'] == issues_list[i]
    
    def test_insert_compliance_issues_dict_without_issue_key(self):
        """Test inserting compliance issues with dict that doesn't have 'issue' key."""
        issues_list = [
            {"description": "This dict doesn't have 'issue' key"},
            {"other_field": "Another dict without 'issue' key"}
        ]
        
        success = insert_compliance_issues(self.run_id, issues_list)
        assert success is True
        
        # Verify data in database - should store string representation
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM compliance_issues WHERE run_id = ?", (self.run_id,))
            count = cursor.fetchone()['count']
            assert count == 2


class TestInsertNotificationEvent:
    """Test insert_notification_event write API."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        # Reset settings singleton
        reset_settings()
        
        # Create temporary database path
        self.temp_dir = tempfile.mkdtemp()
        self.temp_db = os.path.join(self.temp_dir, 'test_incidents.db')
        
        # Set environment variable for test database
        os.environ['DB_PATH'] = self.temp_db
        
        # Initialize database
        initialize_database()
        
        # Create a test pipeline run
        self.run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
    
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
    
    def test_insert_notification_event_basic(self):
        """Test basic notification event insertion."""
        channel = "pushover"
        status = "success"
        response = '{"status": 1, "request": "abc123"}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        
        # Verify success
        assert success is True
    
    def test_insert_notification_event_data_verification(self):
        """Test notification event data is correctly stored."""
        channel = "email"
        status = "success"
        response = '{"message_id": "xyz789", "sent_at": "2025-11-18T10:30:00"}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
            assert row['channel'] == channel
            assert row['status'] == status
            assert row['response'] == response
    
    def test_insert_notification_event_failed_status(self):
        """Test notification event insertion with failed status."""
        channel = "slack"
        status = "failed"
        response = '{"error": "Connection timeout", "code": 500}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['status'] == "failed"
            assert row['response'] == response
    
    def test_insert_notification_event_pending_status(self):
        """Test notification event insertion with pending status."""
        channel = "sms"
        status = "pending"
        response = '{"queued": true, "queue_id": "q123"}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['status'] == "pending"
    
    def test_insert_multiple_notification_events(self):
        """Test inserting multiple notification events for same run."""
        events = [
            ("pushover", "success", '{"status": 1}'),
            ("email", "success", '{"message_id": "abc"}'),
            ("slack", "failed", '{"error": "timeout"}')
        ]
        
        for channel, status, response in events:
            success = insert_notification_event(self.run_id, channel, status, response)
            assert success is True
        
        # Verify all events are in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM notification_events WHERE run_id = ?", (self.run_id,))
            count = cursor.fetchone()['count']
            assert count == 3
    
    def test_insert_notification_events_multiple_runs(self):
        """Test inserting notification events for multiple runs."""
        # Create additional pipeline runs
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Insert notification events for each run
        success_1 = insert_notification_event(self.run_id, "pushover", "success", '{"status": 1}')
        success_2 = insert_notification_event(run_id_2, "email", "success", '{"message_id": "xyz"}')
        success_3 = insert_notification_event(run_id_3, "slack", "failed", '{"error": "timeout"}')
        
        assert success_1 is True
        assert success_2 is True
        assert success_3 is True
        
        # Verify counts for each run
        with get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) as count FROM notification_events WHERE run_id = ?", (self.run_id,))
            assert cursor.fetchone()['count'] == 1
            
            cursor.execute("SELECT COUNT(*) as count FROM notification_events WHERE run_id = ?", (run_id_2,))
            assert cursor.fetchone()['count'] == 1
            
            cursor.execute("SELECT COUNT(*) as count FROM notification_events WHERE run_id = ?", (run_id_3,))
            assert cursor.fetchone()['count'] == 1
    
    def test_insert_notification_event_with_invalid_run_id(self):
        """Test notification event insertion with non-existent run_id."""
        invalid_run_id = 99999
        channel = "pushover"
        status = "success"
        response = '{"status": 1}'
        
        # This should fail due to foreign key constraint
        success = insert_notification_event(invalid_run_id, channel, status, response)
        assert success is False
    
    def test_insert_notification_event_transaction_commit(self):
        """Test that insert commits transaction correctly."""
        channel = "pushover"
        status = "success"
        response = '{"status": 1, "request": "abc123"}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Open a new connection to verify commit
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['run_id'] == self.run_id
    
    def test_insert_notification_event_with_empty_response(self):
        """Test notification event insertion with empty response."""
        channel = "pushover"
        status = "success"
        response = ""
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['response'] == ""
    
    def test_insert_notification_event_with_long_response(self):
        """Test notification event insertion with long response text."""
        channel = "pushover"
        status = "success"
        long_response = '{"data": "' + ("x" * 10000) + '"}'
        
        success = insert_notification_event(self.run_id, channel, status, long_response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['response'] == long_response
    
    def test_insert_notification_event_with_special_characters(self):
        """Test notification event insertion with special characters in response."""
        channel = "pushover"
        status = "success"
        response = '{"message": "Test with \'quotes\' and \"double quotes\" and unicode: 你好 🚀"}'
        
        success = insert_notification_event(self.run_id, channel, status, response)
        assert success is True
        
        # Verify data in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM notification_events WHERE run_id = ?", (self.run_id,))
            row = cursor.fetchone()
            
            assert row is not None
            assert row['response'] == response
    
    def test_insert_notification_event_different_channels(self):
        """Test notification event insertion with different channel types."""
        channels = ["pushover", "email", "slack", "sms", "webhook", "pagerduty"]
        
        for i, channel in enumerate(channels):
            success = insert_notification_event(
                self.run_id,
                channel,
                "success",
                f'{{"channel": "{channel}", "index": {i}}}'
            )
            assert success is True
        
        # Verify all channels are in database
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT channel FROM notification_events WHERE run_id = ? ORDER BY id", (self.run_id,))
            rows = cursor.fetchall()
            
            assert len(rows) == len(channels)
            for i, row in enumerate(rows):
                assert row['channel'] == channels[i]
