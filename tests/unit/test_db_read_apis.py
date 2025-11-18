"""
Unit tests for database read APIs.
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
    get_pipeline_runs,
    insert_governance_analysis,
    get_governance_history,
    get_notifications,
    get_dashboard_metrics
)
from config.settings_loader import reset_settings


class TestGetPipelineRuns:
    """Test get_pipeline_runs read API."""
    
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
    
    def test_get_pipeline_runs_empty_database(self):
        """Test get_pipeline_runs with empty database."""
        runs = get_pipeline_runs()
        
        # Verify empty list is returned
        assert runs == []
        assert isinstance(runs, list)
    
    def test_get_pipeline_runs_single_record(self):
        """Test get_pipeline_runs with single record."""
        # Insert a pipeline run
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 5
        raw_data_path = "data/samples/sample_logs.txt"
        
        run_id = insert_pipeline_run(timestamp, alerts_count, raw_data_path)
        
        # Retrieve pipeline runs
        runs = get_pipeline_runs()
        
        # Verify results
        assert len(runs) == 1
        assert runs[0]['id'] == run_id
        assert runs[0]['timestamp'] == timestamp
        assert runs[0]['alerts_count'] == alerts_count
        assert runs[0]['raw_data_path'] == raw_data_path
    
    def test_get_pipeline_runs_multiple_records(self):
        """Test get_pipeline_runs with multiple records."""
        # Insert multiple pipeline runs
        runs_data = [
            ("2025-11-18T10:00:00", 5, "data/samples/log1.txt"),
            ("2025-11-18T11:00:00", 3, None),
            ("2025-11-18T12:00:00", 8, "data/samples/log2.txt"),
        ]
        
        inserted_ids = []
        for timestamp, alerts_count, raw_data_path in runs_data:
            run_id = insert_pipeline_run(timestamp, alerts_count, raw_data_path)
            inserted_ids.append(run_id)
        
        # Retrieve pipeline runs
        runs = get_pipeline_runs()
        
        # Verify results
        assert len(runs) == 3
        
        # Verify all inserted runs are present
        retrieved_ids = [run['id'] for run in runs]
        for inserted_id in inserted_ids:
            assert inserted_id in retrieved_ids
    
    def test_get_pipeline_runs_ordered_by_timestamp_desc(self):
        """Test that get_pipeline_runs returns records ordered by timestamp descending."""
        # Insert pipeline runs in non-chronological order
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        run_id_2 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        run_id_3 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        
        # Retrieve pipeline runs
        runs = get_pipeline_runs()
        
        # Verify results are ordered by timestamp descending (most recent first)
        assert len(runs) == 3
        assert runs[0]['id'] == run_id_2  # 12:00:00 (most recent)
        assert runs[1]['id'] == run_id_3  # 11:00:00
        assert runs[2]['id'] == run_id_1  # 10:00:00 (oldest)
    
    def test_get_pipeline_runs_with_limit(self):
        """Test get_pipeline_runs with limit parameter."""
        # Insert 5 pipeline runs
        for i in range(5):
            insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
        
        # Retrieve with limit
        runs = get_pipeline_runs(limit=3)
        
        # Verify only 3 most recent runs are returned
        assert len(runs) == 3
    
    def test_get_pipeline_runs_with_limit_larger_than_records(self):
        """Test get_pipeline_runs with limit larger than available records."""
        # Insert 2 pipeline runs
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T11:00:00", 3)
        
        # Retrieve with limit of 10
        runs = get_pipeline_runs(limit=10)
        
        # Verify all 2 runs are returned
        assert len(runs) == 2
    
    def test_get_pipeline_runs_with_limit_zero(self):
        """Test get_pipeline_runs with limit of 0."""
        # Insert pipeline runs
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T11:00:00", 3)
        
        # Retrieve with limit of 0
        runs = get_pipeline_runs(limit=0)
        
        # Verify empty list is returned
        assert len(runs) == 0
    
    def test_get_pipeline_runs_with_limit_one(self):
        """Test get_pipeline_runs with limit of 1."""
        # Insert multiple pipeline runs
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        
        # Retrieve with limit of 1
        runs = get_pipeline_runs(limit=1)
        
        # Verify only the most recent run is returned
        assert len(runs) == 1
        assert runs[0]['id'] == run_id_2
    
    def test_get_pipeline_runs_without_limit(self):
        """Test get_pipeline_runs without limit returns all records."""
        # Insert 10 pipeline runs
        for i in range(10):
            insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
        
        # Retrieve without limit
        runs = get_pipeline_runs()
        
        # Verify all 10 runs are returned
        assert len(runs) == 10
    
    def test_get_pipeline_runs_with_none_limit(self):
        """Test get_pipeline_runs with explicit None limit."""
        # Insert pipeline runs
        for i in range(5):
            insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
        
        # Retrieve with explicit None limit
        runs = get_pipeline_runs(limit=None)
        
        # Verify all 5 runs are returned
        assert len(runs) == 5
    
    def test_get_pipeline_runs_returns_dict_format(self):
        """Test that get_pipeline_runs returns dictionaries with correct keys."""
        # Insert a pipeline run
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5, "data/samples/log.txt")
        
        # Retrieve pipeline runs
        runs = get_pipeline_runs()
        
        # Verify dictionary format
        assert len(runs) == 1
        run = runs[0]
        
        assert isinstance(run, dict)
        assert 'id' in run
        assert 'timestamp' in run
        assert 'alerts_count' in run
        assert 'raw_data_path' in run
        
        assert run['id'] == run_id
        assert run['timestamp'] == "2025-11-18T10:30:00"
        assert run['alerts_count'] == 5
        assert run['raw_data_path'] == "data/samples/log.txt"
    
    def test_get_pipeline_runs_with_null_raw_data_path(self):
        """Test get_pipeline_runs correctly handles NULL raw_data_path."""
        # Insert a pipeline run without raw_data_path
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5)
        
        # Retrieve pipeline runs
        runs = get_pipeline_runs()
        
        # Verify NULL is returned as None
        assert len(runs) == 1
        assert runs[0]['raw_data_path'] is None


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])


class TestGetGovernanceHistory:
    """Test get_governance_history read API."""
    
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
    
    def test_get_governance_history_empty_database(self):
        """Test get_governance_history with empty database."""
        history = get_governance_history()
        
        # Verify empty list is returned
        assert history == []
        assert isinstance(history, list)
    
    def test_get_governance_history_single_record(self):
        """Test get_governance_history with single record."""
        # Insert a pipeline run
        timestamp = "2025-11-18T10:30:00"
        run_id = insert_pipeline_run(timestamp, 5)
        
        # Insert governance analysis
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": "Multiple compliance issues detected"
        }
        insert_governance_analysis(run_id, gov_dict)
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify results
        assert len(history) == 1
        assert history[0]['run_id'] == run_id
        assert history[0]['timestamp'] == timestamp
        assert history[0]['risk'] == "medium"
        assert history[0]['escalation'] == "required"
        assert history[0]['commentary'] == "Multiple compliance issues detected"
    
    def test_get_governance_history_multiple_records(self):
        """Test get_governance_history with multiple records."""
        # Insert multiple pipeline runs with governance analyses
        runs_data = [
            ("2025-11-18T10:00:00", {"risk": "low", "escalation": "none", "commentary": "All clear"}),
            ("2025-11-18T11:00:00", {"risk": "high", "escalation": "immediate", "commentary": "Critical issue"}),
            ("2025-11-18T12:00:00", {"risk": "medium", "escalation": "required", "commentary": "Review needed"}),
        ]
        
        for timestamp, gov_dict in runs_data:
            run_id = insert_pipeline_run(timestamp, 5)
            insert_governance_analysis(run_id, gov_dict)
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify results
        assert len(history) == 3
    
    def test_get_governance_history_ordered_by_timestamp_desc(self):
        """Test that get_governance_history returns records ordered by timestamp descending."""
        # Insert pipeline runs with governance analyses in non-chronological order
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_governance_analysis(run_id_1, {"risk": "low", "escalation": "none", "commentary": "First"})
        
        run_id_2 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        insert_governance_analysis(run_id_2, {"risk": "high", "escalation": "immediate", "commentary": "Third"})
        
        run_id_3 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_governance_analysis(run_id_3, {"risk": "medium", "escalation": "required", "commentary": "Second"})
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify results are ordered by timestamp descending (most recent first)
        assert len(history) == 3
        assert history[0]['run_id'] == run_id_2  # 12:00:00 (most recent)
        assert history[0]['commentary'] == "Third"
        assert history[1]['run_id'] == run_id_3  # 11:00:00
        assert history[1]['commentary'] == "Second"
        assert history[2]['run_id'] == run_id_1  # 10:00:00 (oldest)
        assert history[2]['commentary'] == "First"
    
    def test_get_governance_history_with_limit(self):
        """Test get_governance_history with limit parameter."""
        # Insert 5 pipeline runs with governance analyses
        for i in range(5):
            run_id = insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
            insert_governance_analysis(run_id, {"risk": "low", "escalation": "none", "commentary": f"Run {i}"})
        
        # Retrieve with limit
        history = get_governance_history(limit=3)
        
        # Verify only 3 most recent records are returned
        assert len(history) == 3
    
    def test_get_governance_history_with_limit_larger_than_records(self):
        """Test get_governance_history with limit larger than available records."""
        # Insert 2 pipeline runs with governance analyses
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_governance_analysis(run_id_1, {"risk": "low", "escalation": "none", "commentary": "First"})
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_governance_analysis(run_id_2, {"risk": "medium", "escalation": "required", "commentary": "Second"})
        
        # Retrieve with limit of 10
        history = get_governance_history(limit=10)
        
        # Verify all 2 records are returned
        assert len(history) == 2
    
    def test_get_governance_history_with_limit_zero(self):
        """Test get_governance_history with limit of 0."""
        # Insert pipeline runs with governance analyses
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_governance_analysis(run_id, {"risk": "low", "escalation": "none", "commentary": "Test"})
        
        # Retrieve with limit of 0
        history = get_governance_history(limit=0)
        
        # Verify empty list is returned
        assert len(history) == 0
    
    def test_get_governance_history_with_limit_one(self):
        """Test get_governance_history with limit of 1."""
        # Insert multiple pipeline runs with governance analyses
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_governance_analysis(run_id_1, {"risk": "low", "escalation": "none", "commentary": "First"})
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_governance_analysis(run_id_2, {"risk": "high", "escalation": "immediate", "commentary": "Second"})
        
        # Retrieve with limit of 1
        history = get_governance_history(limit=1)
        
        # Verify only the most recent record is returned
        assert len(history) == 1
        assert history[0]['run_id'] == run_id_2
        assert history[0]['commentary'] == "Second"
    
    def test_get_governance_history_without_limit(self):
        """Test get_governance_history without limit returns all records."""
        # Insert 10 pipeline runs with governance analyses
        for i in range(10):
            run_id = insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
            insert_governance_analysis(run_id, {"risk": "low", "escalation": "none", "commentary": f"Run {i}"})
        
        # Retrieve without limit
        history = get_governance_history()
        
        # Verify all 10 records are returned
        assert len(history) == 10
    
    def test_get_governance_history_with_none_limit(self):
        """Test get_governance_history with explicit None limit."""
        # Insert pipeline runs with governance analyses
        for i in range(5):
            run_id = insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
            insert_governance_analysis(run_id, {"risk": "low", "escalation": "none", "commentary": f"Run {i}"})
        
        # Retrieve with explicit None limit
        history = get_governance_history(limit=None)
        
        # Verify all 5 records are returned
        assert len(history) == 5
    
    def test_get_governance_history_returns_dict_format(self):
        """Test that get_governance_history returns dictionaries with correct keys."""
        # Insert a pipeline run with governance analysis
        timestamp = "2025-11-18T10:30:00"
        run_id = insert_pipeline_run(timestamp, 5)
        gov_dict = {
            "risk": "medium",
            "escalation": "required",
            "commentary": "Test commentary"
        }
        insert_governance_analysis(run_id, gov_dict)
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify dictionary format
        assert len(history) == 1
        record = history[0]
        
        assert isinstance(record, dict)
        assert 'id' in record
        assert 'run_id' in record
        assert 'timestamp' in record
        assert 'risk' in record
        assert 'escalation' in record
        assert 'commentary' in record
        
        assert record['run_id'] == run_id
        assert record['timestamp'] == timestamp
        assert record['risk'] == "medium"
        assert record['escalation'] == "required"
        assert record['commentary'] == "Test commentary"
    
    def test_get_governance_history_with_null_fields(self):
        """Test get_governance_history correctly handles NULL fields."""
        # Insert a pipeline run with governance analysis containing None values
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5)
        gov_dict = {
            "risk": None,
            "escalation": None,
            "commentary": None
        }
        insert_governance_analysis(run_id, gov_dict)
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify NULL values are returned as None
        assert len(history) == 1
        assert history[0]['risk'] is None
        assert history[0]['escalation'] is None
        assert history[0]['commentary'] is None
    
    def test_get_governance_history_only_returns_runs_with_governance(self):
        """Test that get_governance_history only returns runs that have governance analysis."""
        # Insert pipeline runs, but only add governance analysis to some
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_governance_analysis(run_id_1, {"risk": "low", "escalation": "none", "commentary": "First"})
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        # No governance analysis for run_id_2
        
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        insert_governance_analysis(run_id_3, {"risk": "high", "escalation": "immediate", "commentary": "Third"})
        
        # Retrieve governance history
        history = get_governance_history()
        
        # Verify only runs with governance analysis are returned
        assert len(history) == 2
        returned_run_ids = [record['run_id'] for record in history]
        assert run_id_1 in returned_run_ids
        assert run_id_3 in returned_run_ids
        assert run_id_2 not in returned_run_ids



class TestGetNotifications:
    """Test get_notifications read API."""
    
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
    
    def test_get_notifications_empty_database(self):
        """Test get_notifications with empty database."""
        notifications = get_notifications()
        
        # Verify empty list is returned
        assert notifications == []
        assert isinstance(notifications, list)
    
    def test_get_notifications_single_record(self):
        """Test get_notifications with single record."""
        # Insert a pipeline run
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5)
        
        # Insert notification event
        from db.db_util import insert_notification_event
        insert_notification_event(run_id, "pushover", "success", '{"status": 1}')
        
        # Retrieve notifications
        notifications = get_notifications()
        
        # Verify results
        assert len(notifications) == 1
        assert notifications[0]['run_id'] == run_id
        assert notifications[0]['channel'] == "pushover"
        assert notifications[0]['status'] == "success"
        assert notifications[0]['response'] == '{"status": 1}'
    
    def test_get_notifications_multiple_records(self):
        """Test get_notifications with multiple records."""
        # Insert multiple pipeline runs with notifications
        from db.db_util import insert_notification_event
        
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id_1, "email", "success", "Email sent")
        insert_notification_event(run_id_1, "slack", "failed", "Connection timeout")
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_notification_event(run_id_2, "pushover", "success", '{"status": 1}')
        
        # Retrieve all notifications
        notifications = get_notifications()
        
        # Verify results
        assert len(notifications) == 3
    
    def test_get_notifications_filtered_by_run_id(self):
        """Test get_notifications filtered by specific run_id."""
        # Insert multiple pipeline runs with notifications
        from db.db_util import insert_notification_event
        
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id_1, "email", "success", "Email sent")
        insert_notification_event(run_id_1, "slack", "success", "Slack sent")
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_notification_event(run_id_2, "pushover", "success", '{"status": 1}')
        
        # Retrieve notifications for run_id_1 only
        notifications = get_notifications(run_id=run_id_1)
        
        # Verify only notifications for run_id_1 are returned
        assert len(notifications) == 2
        for notification in notifications:
            assert notification['run_id'] == run_id_1
    
    def test_get_notifications_filtered_by_nonexistent_run_id(self):
        """Test get_notifications filtered by non-existent run_id."""
        # Insert a pipeline run with notification
        from db.db_util import insert_notification_event
        
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id, "email", "success", "Email sent")
        
        # Retrieve notifications for non-existent run_id
        notifications = get_notifications(run_id=9999)
        
        # Verify empty list is returned
        assert notifications == []
    
    def test_get_notifications_ordered_by_id_desc(self):
        """Test that get_notifications returns records ordered by id descending."""
        # Insert pipeline run with multiple notifications
        from db.db_util import insert_notification_event
        
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id, "email", "success", "First")
        insert_notification_event(run_id, "slack", "success", "Second")
        insert_notification_event(run_id, "pushover", "success", "Third")
        
        # Retrieve notifications
        notifications = get_notifications()
        
        # Verify results are ordered by id descending (most recent first)
        assert len(notifications) == 3
        assert notifications[0]['response'] == "Third"
        assert notifications[1]['response'] == "Second"
        assert notifications[2]['response'] == "First"
    
    def test_get_notifications_returns_dict_format(self):
        """Test that get_notifications returns dictionaries with correct keys."""
        # Insert a pipeline run with notification
        from db.db_util import insert_notification_event
        
        run_id = insert_pipeline_run("2025-11-18T10:30:00", 5)
        insert_notification_event(run_id, "pushover", "success", '{"status": 1}')
        
        # Retrieve notifications
        notifications = get_notifications()
        
        # Verify dictionary format
        assert len(notifications) == 1
        notification = notifications[0]
        
        assert isinstance(notification, dict)
        assert 'id' in notification
        assert 'run_id' in notification
        assert 'channel' in notification
        assert 'status' in notification
        assert 'response' in notification
        
        assert notification['run_id'] == run_id
        assert notification['channel'] == "pushover"
        assert notification['status'] == "success"
        assert notification['response'] == '{"status": 1}'
    
    def test_get_notifications_with_none_run_id(self):
        """Test get_notifications with explicit None run_id returns all notifications."""
        # Insert multiple pipeline runs with notifications
        from db.db_util import insert_notification_event
        
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id_1, "email", "success", "Email sent")
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_notification_event(run_id_2, "slack", "success", "Slack sent")
        
        # Retrieve with explicit None run_id
        notifications = get_notifications(run_id=None)
        
        # Verify all notifications are returned
        assert len(notifications) == 2
    
    def test_get_notifications_multiple_channels_same_run(self):
        """Test get_notifications with multiple channels for same run."""
        # Insert a pipeline run with multiple notification channels
        from db.db_util import insert_notification_event
        
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id, "email", "success", "Email sent")
        insert_notification_event(run_id, "slack", "success", "Slack sent")
        insert_notification_event(run_id, "pushover", "failed", "Pushover failed")
        
        # Retrieve notifications for this run
        notifications = get_notifications(run_id=run_id)
        
        # Verify all channels are returned
        assert len(notifications) == 3
        channels = [n['channel'] for n in notifications]
        assert "email" in channels
        assert "slack" in channels
        assert "pushover" in channels
    
    def test_get_notifications_different_statuses(self):
        """Test get_notifications with different notification statuses."""
        # Insert a pipeline run with notifications of different statuses
        from db.db_util import insert_notification_event
        
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_notification_event(run_id, "email", "success", "Email sent")
        insert_notification_event(run_id, "slack", "failed", "Connection timeout")
        insert_notification_event(run_id, "pushover", "pending", "Queued")
        
        # Retrieve notifications
        notifications = get_notifications(run_id=run_id)
        
        # Verify all statuses are returned
        assert len(notifications) == 3
        statuses = [n['status'] for n in notifications]
        assert "success" in statuses
        assert "failed" in statuses
        assert "pending" in statuses



class TestGetDashboardMetrics:
    """Test get_dashboard_metrics read API."""
    
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
    
    def test_get_dashboard_metrics_empty_database(self):
        """Test get_dashboard_metrics with empty database."""
        metrics = get_dashboard_metrics()
        
        # Verify default values are returned
        assert isinstance(metrics, dict)
        assert metrics['total_executions'] == 0
        assert metrics['total_incidents'] == 0
        assert metrics['avg_incidents_per_run'] == 0.0
        assert metrics['last_execution_timestamp'] is None
    
    def test_get_dashboard_metrics_single_run(self):
        """Test get_dashboard_metrics with single pipeline run."""
        # Insert a pipeline run
        timestamp = "2025-11-18T10:30:00"
        alerts_count = 5
        insert_pipeline_run(timestamp, alerts_count)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify results
        assert metrics['total_executions'] == 1
        assert metrics['total_incidents'] == 5
        assert metrics['avg_incidents_per_run'] == 5.0
        assert metrics['last_execution_timestamp'] == timestamp
    
    def test_get_dashboard_metrics_multiple_runs(self):
        """Test get_dashboard_metrics with multiple pipeline runs."""
        # Insert multiple pipeline runs
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify results
        assert metrics['total_executions'] == 3
        assert metrics['total_incidents'] == 16  # 5 + 3 + 8
        assert abs(metrics['avg_incidents_per_run'] - 5.333) < 0.01  # Average of 5, 3, 8
        assert metrics['last_execution_timestamp'] == "2025-11-18T12:00:00"
    
    def test_get_dashboard_metrics_zero_incidents(self):
        """Test get_dashboard_metrics with runs that have zero incidents."""
        # Insert pipeline runs with zero incidents
        insert_pipeline_run("2025-11-18T10:00:00", 0)
        insert_pipeline_run("2025-11-18T11:00:00", 0)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify results
        assert metrics['total_executions'] == 2
        assert metrics['total_incidents'] == 0
        assert metrics['avg_incidents_per_run'] == 0.0
        assert metrics['last_execution_timestamp'] == "2025-11-18T11:00:00"
    
    def test_get_dashboard_metrics_mixed_incidents(self):
        """Test get_dashboard_metrics with mixed incident counts."""
        # Insert pipeline runs with various incident counts
        insert_pipeline_run("2025-11-18T10:00:00", 0)
        insert_pipeline_run("2025-11-18T11:00:00", 10)
        insert_pipeline_run("2025-11-18T12:00:00", 5)
        insert_pipeline_run("2025-11-18T13:00:00", 0)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify results
        assert metrics['total_executions'] == 4
        assert metrics['total_incidents'] == 15  # 0 + 10 + 5 + 0
        assert metrics['avg_incidents_per_run'] == 3.75  # 15 / 4
        assert metrics['last_execution_timestamp'] == "2025-11-18T13:00:00"
    
    def test_get_dashboard_metrics_returns_dict_format(self):
        """Test that get_dashboard_metrics returns dictionary with correct keys."""
        # Insert a pipeline run
        insert_pipeline_run("2025-11-18T10:30:00", 5)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify dictionary format
        assert isinstance(metrics, dict)
        assert 'total_executions' in metrics
        assert 'total_incidents' in metrics
        assert 'avg_incidents_per_run' in metrics
        assert 'last_execution_timestamp' in metrics
        
        # Verify data types
        assert isinstance(metrics['total_executions'], int)
        assert isinstance(metrics['total_incidents'], int)
        assert isinstance(metrics['avg_incidents_per_run'], float)
        assert isinstance(metrics['last_execution_timestamp'], str) or metrics['last_execution_timestamp'] is None
    
    def test_get_dashboard_metrics_most_recent_timestamp(self):
        """Test that get_dashboard_metrics returns the most recent timestamp."""
        # Insert pipeline runs in non-chronological order
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T14:00:00", 8)
        insert_pipeline_run("2025-11-18T12:00:00", 3)
        insert_pipeline_run("2025-11-18T11:00:00", 2)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify the most recent timestamp is returned
        assert metrics['last_execution_timestamp'] == "2025-11-18T14:00:00"
    
    def test_get_dashboard_metrics_large_numbers(self):
        """Test get_dashboard_metrics with large incident counts."""
        # Insert pipeline runs with large incident counts
        insert_pipeline_run("2025-11-18T10:00:00", 1000)
        insert_pipeline_run("2025-11-18T11:00:00", 2000)
        insert_pipeline_run("2025-11-18T12:00:00", 1500)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify results
        assert metrics['total_executions'] == 3
        assert metrics['total_incidents'] == 4500
        assert metrics['avg_incidents_per_run'] == 1500.0
    
    def test_get_dashboard_metrics_average_precision(self):
        """Test that get_dashboard_metrics returns average with proper precision."""
        # Insert pipeline runs that result in non-integer average
        insert_pipeline_run("2025-11-18T10:00:00", 7)
        insert_pipeline_run("2025-11-18T11:00:00", 8)
        insert_pipeline_run("2025-11-18T12:00:00", 9)
        
        # Retrieve dashboard metrics
        metrics = get_dashboard_metrics()
        
        # Verify average is a float with proper precision
        assert metrics['avg_incidents_per_run'] == 8.0
        assert isinstance(metrics['avg_incidents_per_run'], float)



class TestGetComplianceStats:
    """Test get_compliance_stats read API."""
    
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
    
    def test_get_compliance_stats_empty_database(self):
        """Test get_compliance_stats with empty database."""
        from db.db_util import get_compliance_stats
        
        stats = get_compliance_stats()
        
        # Verify default values are returned
        assert isinstance(stats, dict)
        assert stats['total_issues'] == 0
        assert stats['runs_with_issues'] == 0
        assert stats['runs_without_issues'] == 0
        assert stats['avg_issues_per_run'] == 0.0
    
    def test_get_compliance_stats_no_issues(self):
        """Test get_compliance_stats with pipeline runs but no compliance issues."""
        from db.db_util import get_compliance_stats
        
        # Insert pipeline runs without compliance issues
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T11:00:00", 3)
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 0
        assert stats['runs_with_issues'] == 0
        assert stats['runs_without_issues'] == 2
        assert stats['avg_issues_per_run'] == 0.0
    
    def test_get_compliance_stats_single_run_with_issues(self):
        """Test get_compliance_stats with single run containing compliance issues."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert a pipeline run with compliance issues
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        issues = [
            "Missing security patch for CVE-2024-1234",
            "Unauthorized access attempt detected"
        ]
        insert_compliance_issues(run_id, issues)
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 2
        assert stats['runs_with_issues'] == 1
        assert stats['runs_without_issues'] == 0
        assert stats['avg_issues_per_run'] == 2.0
    
    def test_get_compliance_stats_multiple_runs_with_issues(self):
        """Test get_compliance_stats with multiple runs containing compliance issues."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert multiple pipeline runs with compliance issues
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_compliance_issues(run_id_1, ["Issue 1", "Issue 2"])
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_compliance_issues(run_id_2, ["Issue 3", "Issue 4", "Issue 5"])
        
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        insert_compliance_issues(run_id_3, ["Issue 6"])
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 6
        assert stats['runs_with_issues'] == 3
        assert stats['runs_without_issues'] == 0
        assert stats['avg_issues_per_run'] == 2.0  # 6 issues / 3 runs
    
    def test_get_compliance_stats_mixed_runs(self):
        """Test get_compliance_stats with some runs having issues and some without."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert pipeline runs with mixed compliance status
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_compliance_issues(run_id_1, ["Issue 1", "Issue 2"])
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        # No compliance issues for run_id_2
        
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        insert_compliance_issues(run_id_3, ["Issue 3"])
        
        run_id_4 = insert_pipeline_run("2025-11-18T13:00:00", 2)
        # No compliance issues for run_id_4
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 3
        assert stats['runs_with_issues'] == 2
        assert stats['runs_without_issues'] == 2
        assert stats['avg_issues_per_run'] == 0.75  # 3 issues / 4 runs
    
    def test_get_compliance_stats_returns_dict_format(self):
        """Test that get_compliance_stats returns dictionary with correct keys."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert a pipeline run with compliance issues
        run_id = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_compliance_issues(run_id, ["Issue 1"])
        
        stats = get_compliance_stats()
        
        # Verify dictionary format
        assert isinstance(stats, dict)
        assert 'total_issues' in stats
        assert 'runs_with_issues' in stats
        assert 'runs_without_issues' in stats
        assert 'avg_issues_per_run' in stats
        
        # Verify data types
        assert isinstance(stats['total_issues'], int)
        assert isinstance(stats['runs_with_issues'], int)
        assert isinstance(stats['runs_without_issues'], int)
        assert isinstance(stats['avg_issues_per_run'], float)
    
    def test_get_compliance_stats_large_numbers(self):
        """Test get_compliance_stats with large numbers of issues."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert pipeline runs with many compliance issues
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_compliance_issues(run_id_1, [f"Issue {i}" for i in range(100)])
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_compliance_issues(run_id_2, [f"Issue {i}" for i in range(50)])
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 150
        assert stats['runs_with_issues'] == 2
        assert stats['runs_without_issues'] == 0
        assert stats['avg_issues_per_run'] == 75.0
    
    def test_get_compliance_stats_average_precision(self):
        """Test that get_compliance_stats returns average with proper precision."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert pipeline runs that result in non-integer average
        run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_compliance_issues(run_id_1, ["Issue 1", "Issue 2"])
        
        run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_compliance_issues(run_id_2, ["Issue 3"])
        
        run_id_3 = insert_pipeline_run("2025-11-18T12:00:00", 8)
        # No issues
        
        stats = get_compliance_stats()
        
        # Verify average is a float with proper precision
        # 3 issues / 3 runs = 1.0
        assert stats['avg_issues_per_run'] == 1.0
        assert isinstance(stats['avg_issues_per_run'], float)
    
    def test_get_compliance_stats_all_runs_without_issues(self):
        """Test get_compliance_stats when all runs have no compliance issues."""
        from db.db_util import get_compliance_stats
        
        # Insert multiple pipeline runs without compliance issues
        insert_pipeline_run("2025-11-18T10:00:00", 5)
        insert_pipeline_run("2025-11-18T11:00:00", 3)
        insert_pipeline_run("2025-11-18T12:00:00", 8)
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 0
        assert stats['runs_with_issues'] == 0
        assert stats['runs_without_issues'] == 3
        assert stats['avg_issues_per_run'] == 0.0
    
    def test_get_compliance_stats_single_issue_per_run(self):
        """Test get_compliance_stats when each run has exactly one issue."""
        from db.db_util import get_compliance_stats, insert_compliance_issues
        
        # Insert pipeline runs with one issue each
        for i in range(5):
            run_id = insert_pipeline_run(f"2025-11-18T{10+i:02d}:00:00", i)
            insert_compliance_issues(run_id, [f"Issue {i}"])
        
        stats = get_compliance_stats()
        
        # Verify results
        assert stats['total_issues'] == 5
        assert stats['runs_with_issues'] == 5
        assert stats['runs_without_issues'] == 0
        assert stats['avg_issues_per_run'] == 1.0
