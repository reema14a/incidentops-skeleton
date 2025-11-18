"""
Unit tests for database chart data APIs.

Tests the new DB functions that provide chart data for the Dashboard:
- get_severity_distribution()
- get_category_distribution()
- get_timeline_data()
"""

import os
import sys
import tempfile
import pytest
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from db.db_util import (
    get_severity_distribution,
    get_category_distribution,
    get_timeline_data,
    insert_pipeline_run,
    insert_audit_summary,
    get_connection,
    initialize_database
)
from config.settings_loader import reset_settings


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Reset settings singleton
    reset_settings()
    
    # Create temporary database path
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, 'test_incidents.db')
    
    # Set environment variable for test database
    os.environ['DB_PATH'] = db_path
    
    # Reset settings to pick up new environment variable
    reset_settings()
    
    # Initialize the database
    initialize_database()
    
    yield db_path
    
    # Cleanup
    if os.path.exists(db_path):
        os.remove(db_path)
    if os.path.exists(temp_dir):
        os.rmdir(temp_dir)
    
    # Reset settings
    reset_settings()


def test_get_severity_distribution_empty(temp_db):
    """Test get_severity_distribution with no data."""
    result = get_severity_distribution()
    assert result == {}


def test_get_severity_distribution_with_data(temp_db):
    """Test get_severity_distribution with sample data."""
    # Insert a pipeline run
    run_id = insert_pipeline_run("2025-11-18T10:00:00", 10)
    
    # Insert audit summary with severity distribution
    audit_dict = {
        "execution_timestamp": "2025-11-18 10:00:00",
        "total_incidents": 10,
        "stage_outputs": {
            "triage_stage": {
                "severity_distribution": {
                    "critical": 2,
                    "high": 3,
                    "medium": 4,
                    "low": 1
                }
            }
        }
    }
    
    success = insert_audit_summary(run_id, audit_dict)
    assert success is True
    
    # Get severity distribution
    result = get_severity_distribution()
    
    assert result == {
        "critical": 2,
        "high": 3,
        "medium": 4,
        "low": 1
    }


def test_get_severity_distribution_aggregates_multiple_runs(temp_db):
    """Test that get_severity_distribution aggregates across multiple runs."""
    # Insert first run
    run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 5)
    audit_dict_1 = {
        "stage_outputs": {
            "triage_stage": {
                "severity_distribution": {
                    "critical": 1,
                    "high": 2,
                    "medium": 2
                }
            }
        }
    }
    insert_audit_summary(run_id_1, audit_dict_1)
    
    # Insert second run
    run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 4)
    audit_dict_2 = {
        "stage_outputs": {
            "triage_stage": {
                "severity_distribution": {
                    "critical": 2,
                    "medium": 1,
                    "low": 1
                }
            }
        }
    }
    insert_audit_summary(run_id_2, audit_dict_2)
    
    # Get aggregated severity distribution
    result = get_severity_distribution()
    
    assert result == {
        "critical": 3,  # 1 + 2
        "high": 2,      # 2 + 0
        "medium": 3,    # 2 + 1
        "low": 1        # 0 + 1
    }


def test_get_category_distribution_empty(temp_db):
    """Test get_category_distribution with no data."""
    result = get_category_distribution()
    assert result == {}


def test_get_category_distribution_with_data(temp_db):
    """Test get_category_distribution with sample data."""
    # Insert a pipeline run
    run_id = insert_pipeline_run("2025-11-18T10:00:00", 8)
    
    # Insert audit summary with category distribution
    audit_dict = {
        "stage_outputs": {
            "triage_stage": {
                "category_distribution": {
                    "network": 3,
                    "security": 2,
                    "performance": 2,
                    "database": 1
                }
            }
        }
    }
    
    success = insert_audit_summary(run_id, audit_dict)
    assert success is True
    
    # Get category distribution
    result = get_category_distribution()
    
    assert result == {
        "network": 3,
        "security": 2,
        "performance": 2,
        "database": 1
    }


def test_get_category_distribution_aggregates_multiple_runs(temp_db):
    """Test that get_category_distribution aggregates across multiple runs."""
    # Insert first run
    run_id_1 = insert_pipeline_run("2025-11-18T10:00:00", 4)
    audit_dict_1 = {
        "stage_outputs": {
            "triage_stage": {
                "category_distribution": {
                    "network": 2,
                    "security": 2
                }
            }
        }
    }
    insert_audit_summary(run_id_1, audit_dict_1)
    
    # Insert second run
    run_id_2 = insert_pipeline_run("2025-11-18T11:00:00", 3)
    audit_dict_2 = {
        "stage_outputs": {
            "triage_stage": {
                "category_distribution": {
                    "network": 1,
                    "performance": 2
                }
            }
        }
    }
    insert_audit_summary(run_id_2, audit_dict_2)
    
    # Get aggregated category distribution
    result = get_category_distribution()
    
    assert result == {
        "network": 3,      # 2 + 1
        "security": 2,     # 2 + 0
        "performance": 2   # 0 + 2
    }


def test_get_timeline_data_empty(temp_db):
    """Test get_timeline_data with no data."""
    result = get_timeline_data()
    assert result == []


def test_get_timeline_data_with_data(temp_db):
    """Test get_timeline_data with sample data."""
    # Insert pipeline runs
    insert_pipeline_run("2025-11-18T10:00:00", 5)
    insert_pipeline_run("2025-11-18T11:30:00", 3)
    insert_pipeline_run("2025-11-19T09:15:00", 7)
    
    # Get timeline data
    result = get_timeline_data()
    
    assert len(result) == 3
    
    # Check first record
    assert result[0]['date'] == '2025-11-18'
    assert result[0]['time'] == '10:00:00'
    assert result[0]['incidents'] == 5
    
    # Check second record
    assert result[1]['date'] == '2025-11-18'
    assert result[1]['time'] == '11:30:00'
    assert result[1]['incidents'] == 3
    
    # Check third record
    assert result[2]['date'] == '2025-11-19'
    assert result[2]['time'] == '09:15:00'
    assert result[2]['incidents'] == 7


def test_get_timeline_data_handles_different_timestamp_formats(temp_db):
    """Test that get_timeline_data handles both timestamp formats."""
    # Insert with ISO format (with T separator)
    insert_pipeline_run("2025-11-18T10:00:00.123456", 5)
    
    # Insert with space separator  
    insert_pipeline_run("2025-11-18 11:00:00", 3)
    
    # Get timeline data
    result = get_timeline_data()
    
    # Both formats should be parsed successfully
    assert len(result) == 2
    
    # Check that both records have the correct date
    assert all(r['date'] == '2025-11-18' for r in result)
    
    # Check that both records have valid times
    times = {r['time'] for r in result}
    assert '10:00:00' in times
    assert '11:00:00' in times
    
    # Check that incidents are preserved
    incidents = {r['incidents'] for r in result}
    assert 5 in incidents
    assert 3 in incidents


def test_get_timeline_data_ordered_by_timestamp(temp_db):
    """Test that get_timeline_data returns records in chronological order."""
    # Insert in non-chronological order
    insert_pipeline_run("2025-11-19T10:00:00", 7)
    insert_pipeline_run("2025-11-18T10:00:00", 5)
    insert_pipeline_run("2025-11-18T15:00:00", 3)
    
    # Get timeline data
    result = get_timeline_data()
    
    # Should be ordered chronologically
    assert len(result) == 3
    assert result[0]['date'] == '2025-11-18'
    assert result[0]['time'] == '10:00:00'
    assert result[1]['date'] == '2025-11-18'
    assert result[1]['time'] == '15:00:00'
    assert result[2]['date'] == '2025-11-19'
    assert result[2]['time'] == '10:00:00'
