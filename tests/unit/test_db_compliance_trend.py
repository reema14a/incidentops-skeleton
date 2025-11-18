"""
Unit tests for get_compliance_trend() database utility function.
"""
import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path

import pytest

from db import db_util


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create a temporary directory and database file
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_incidents.db')
    
    # Mock the settings to use our temp database
    original_get_db_path = db_util._get_db_path
    db_util._get_db_path = lambda: db_path
    
    # Initialize the database
    db_util.initialize_database()
    
    yield db_path
    
    # Cleanup
    db_util._get_db_path = original_get_db_path
    try:
        os.remove(db_path)
        os.rmdir(temp_dir)
    except:
        pass


def test_get_compliance_trend_empty_database(temp_db):
    """Test get_compliance_trend returns empty list when no data exists."""
    result = db_util.get_compliance_trend()
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_compliance_trend_with_data(temp_db):
    """Test get_compliance_trend returns correct compliance trend data."""
    # Insert test pipeline runs
    timestamp1 = datetime.utcnow().isoformat(timespec="microseconds")
    timestamp2 = datetime.utcnow().isoformat(timespec="microseconds")
    
    run_id1 = db_util.insert_pipeline_run(timestamp1, 5, None)
    run_id2 = db_util.insert_pipeline_run(timestamp2, 10, None)
    
    # Insert compliance issues
    issues1 = ['Security patch missing', 'Configuration drift detected']
    issues2 = ['Unauthorized access attempt']
    
    db_util.insert_compliance_issues(run_id1, issues1)
    db_util.insert_compliance_issues(run_id2, issues2)
    
    # Get compliance trend
    result = db_util.get_compliance_trend()
    
    # Verify results
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Check first record
    assert result[0]['run_id'] == run_id1
    assert result[0]['issue_count'] == 2
    assert result[0]['timestamp'] == timestamp1
    assert 'date' in result[0]
    assert 'time' in result[0]
    
    # Check second record
    assert result[1]['run_id'] == run_id2
    assert result[1]['issue_count'] == 1
    assert result[1]['timestamp'] == timestamp2
    assert 'date' in result[1]
    assert 'time' in result[1]


def test_get_compliance_trend_ordering(temp_db):
    """Test get_compliance_trend returns records in chronological order."""
    # Insert test pipeline runs with different timestamps
    timestamp1 = "2025-11-18T10:00:00.000000"
    timestamp2 = "2025-11-18T11:00:00.000000"
    timestamp3 = "2025-11-18T09:00:00.000000"  # Earlier than timestamp1
    
    run_id1 = db_util.insert_pipeline_run(timestamp1, 5, None)
    run_id2 = db_util.insert_pipeline_run(timestamp2, 10, None)
    run_id3 = db_util.insert_pipeline_run(timestamp3, 3, None)
    
    # Insert compliance issues
    db_util.insert_compliance_issues(run_id1, ['Issue 1'])
    db_util.insert_compliance_issues(run_id2, ['Issue 2', 'Issue 3'])
    db_util.insert_compliance_issues(run_id3, ['Issue 4', 'Issue 5', 'Issue 6'])
    
    # Get compliance trend
    result = db_util.get_compliance_trend()
    
    # Verify chronological ordering (ascending)
    assert len(result) == 3
    assert result[0]['run_id'] == run_id3  # Earliest timestamp
    assert result[0]['issue_count'] == 3
    assert result[1]['run_id'] == run_id1
    assert result[1]['issue_count'] == 1
    assert result[2]['run_id'] == run_id2  # Latest timestamp
    assert result[2]['issue_count'] == 2


def test_get_compliance_trend_zero_issues(temp_db):
    """Test get_compliance_trend includes runs with zero compliance issues."""
    # Insert test pipeline runs
    timestamp1 = datetime.utcnow().isoformat(timespec="microseconds")
    timestamp2 = datetime.utcnow().isoformat(timespec="microseconds")
    
    run_id1 = db_util.insert_pipeline_run(timestamp1, 5, None)
    run_id2 = db_util.insert_pipeline_run(timestamp2, 10, None)
    
    # Insert compliance issues only for run_id1
    db_util.insert_compliance_issues(run_id1, ['Issue 1'])
    # run_id2 has no compliance issues
    
    # Get compliance trend
    result = db_util.get_compliance_trend()
    
    # Should include both runs
    assert len(result) == 2
    assert result[0]['run_id'] == run_id1
    assert result[0]['issue_count'] == 1
    assert result[1]['run_id'] == run_id2
    assert result[1]['issue_count'] == 0  # Zero issues


def test_get_compliance_trend_multiple_issues_per_run(temp_db):
    """Test get_compliance_trend correctly counts multiple issues per run."""
    # Insert test pipeline run
    timestamp = datetime.utcnow().isoformat(timespec="microseconds")
    run_id = db_util.insert_pipeline_run(timestamp, 5, None)
    
    # Insert multiple compliance issues
    issues = [
        'Security patch missing',
        'Configuration drift detected',
        'Unauthorized access attempt',
        'Missing encryption',
        'Weak password policy'
    ]
    
    db_util.insert_compliance_issues(run_id, issues)
    
    # Get compliance trend
    result = db_util.get_compliance_trend()
    
    # Verify count
    assert len(result) == 1
    assert result[0]['run_id'] == run_id
    assert result[0]['issue_count'] == 5


def test_get_compliance_trend_date_time_formatting(temp_db):
    """Test get_compliance_trend formats date and time correctly."""
    # Insert test pipeline run with specific timestamp
    timestamp = "2025-11-18T14:30:45.123456"
    run_id = db_util.insert_pipeline_run(timestamp, 5, None)
    
    # Insert compliance issue
    db_util.insert_compliance_issues(run_id, ['Test issue'])
    
    # Get compliance trend
    result = db_util.get_compliance_trend()
    
    # Verify date and time formatting
    assert len(result) == 1
    assert result[0]['date'] == '2025-11-18'
    assert result[0]['time'] == '14:30:45'
    assert result[0]['timestamp'] == timestamp
