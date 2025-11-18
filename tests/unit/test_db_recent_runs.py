"""
Unit tests for get_recent_runs() database utility function.
"""

import sqlite3
import tempfile
import os
from datetime import datetime
from pathlib import Path

from db.db_util import (
    get_recent_runs,
    insert_pipeline_run,
    insert_audit_summary,
    insert_governance_analysis,
    get_connection,
    initialize_database
)


def test_get_recent_runs_empty_database(monkeypatch):
    """Test get_recent_runs returns empty list when database is empty."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp:
        tmp_db_path = tmp.name
    
    try:
        # Mock the database path
        def mock_get_db_path():
            return tmp_db_path
        
        monkeypatch.setattr('db.db_util._get_db_path', mock_get_db_path)
        
        # Initialize the database
        initialize_database()
        
        # Get recent runs from empty database
        result = get_recent_runs()
        
        assert result == []
        
    finally:
        # Clean up
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_get_recent_runs_with_data(monkeypatch):
    """Test get_recent_runs returns recent pipeline runs with associated data."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp:
        tmp_db_path = tmp.name
    
    try:
        # Mock the database path
        def mock_get_db_path():
            return tmp_db_path
        
        monkeypatch.setattr('db.db_util._get_db_path', mock_get_db_path)
        
        # Initialize the database
        initialize_database()
        
        # Insert test data - 5 pipeline runs
        timestamps = [
            "2025-11-18T10:00:00.000000",
            "2025-11-18T11:00:00.000000",
            "2025-11-18T12:00:00.000000",
            "2025-11-18T13:00:00.000000",
            "2025-11-18T14:00:00.000000"
        ]
        
        run_ids = []
        for i, ts in enumerate(timestamps):
            run_id = insert_pipeline_run(ts, i + 1, f"data/samples/log_{i}.txt")
            run_ids.append(run_id)
            
            # Add audit summary for some runs
            if i % 2 == 0:
                insert_audit_summary(run_id, {
                    "status": "completed",
                    "count": i + 1,
                    "timestamp": ts,
                    "execution_timestamp": ts,
                    "total_incidents": i + 1
                })
            
            # Add governance analysis for some runs
            if i % 3 == 0:
                insert_governance_analysis(run_id, {
                    "risk": "low" if i == 0 else "medium",
                    "escalation": "None required",
                    "commentary": f"Test commentary {i}"
                })
        
        # Get recent runs with default limit (10)
        result = get_recent_runs()
        
        # Should return all 5 runs (less than limit of 10)
        assert len(result) == 5
        
        # Should be ordered by timestamp descending (most recent first)
        assert result[0]['timestamp'] == "2025-11-18T14:00:00.000000"
        assert result[4]['timestamp'] == "2025-11-18T10:00:00.000000"
        
        # Check structure of first result
        assert 'run_id' in result[0]
        assert 'timestamp' in result[0]
        assert 'alerts_count' in result[0]
        assert 'raw_data_path' in result[0]
        assert 'audit_data' in result[0]
        assert 'governance_data' in result[0]
        
        # Verify alerts_count
        assert result[0]['alerts_count'] == 5
        assert result[1]['alerts_count'] == 4
        
        # Verify raw_data_path
        assert result[0]['raw_data_path'] == "data/samples/log_4.txt"
        
    finally:
        # Clean up
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_get_recent_runs_with_limit(monkeypatch):
    """Test get_recent_runs respects the limit parameter."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp:
        tmp_db_path = tmp.name
    
    try:
        # Mock the database path
        def mock_get_db_path():
            return tmp_db_path
        
        monkeypatch.setattr('db.db_util._get_db_path', mock_get_db_path)
        
        # Initialize the database
        initialize_database()
        
        # Insert 10 pipeline runs
        for i in range(10):
            ts = f"2025-11-18T{10+i:02d}:00:00.000000"
            insert_pipeline_run(ts, i + 1, f"data/samples/log_{i}.txt")
        
        # Get recent runs with limit of 3
        result = get_recent_runs(limit=3)
        
        # Should return exactly 3 runs
        assert len(result) == 3
        
        # Should be the 3 most recent
        assert result[0]['timestamp'] == "2025-11-18T19:00:00.000000"
        assert result[1]['timestamp'] == "2025-11-18T18:00:00.000000"
        assert result[2]['timestamp'] == "2025-11-18T17:00:00.000000"
        
    finally:
        # Clean up
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)


def test_get_recent_runs_includes_null_data(monkeypatch):
    """Test get_recent_runs handles runs without audit or governance data."""
    # Create a temporary database
    with tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False) as tmp:
        tmp_db_path = tmp.name
    
    try:
        # Mock the database path
        def mock_get_db_path():
            return tmp_db_path
        
        monkeypatch.setattr('db.db_util._get_db_path', mock_get_db_path)
        
        # Initialize the database
        initialize_database()
        
        # Insert pipeline run without audit or governance data
        ts = "2025-11-18T10:00:00.000000"
        run_id = insert_pipeline_run(ts, 5, "data/samples/log.txt")
        
        # Get recent runs
        result = get_recent_runs()
        
        # Should return the run
        assert len(result) == 1
        assert result[0]['run_id'] == run_id
        assert result[0]['timestamp'] == ts
        assert result[0]['alerts_count'] == 5
        
        # audit_data and governance_data should be None
        assert result[0]['audit_data'] is None
        assert result[0]['governance_data'] is None
        
    finally:
        # Clean up
        if os.path.exists(tmp_db_path):
            os.unlink(tmp_db_path)
