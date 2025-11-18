"""
Unit tests for get_risk_trend() database utility function.
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


def test_get_risk_trend_empty_database(temp_db):
    """Test get_risk_trend returns empty list when no data exists."""
    result = db_util.get_risk_trend()
    
    assert isinstance(result, list)
    assert len(result) == 0


def test_get_risk_trend_with_data(temp_db):
    """Test get_risk_trend returns correct risk trend data."""
    # Insert test pipeline runs
    timestamp1 = datetime.utcnow().isoformat(timespec="microseconds")
    timestamp2 = datetime.utcnow().isoformat(timespec="microseconds")
    
    run_id1 = db_util.insert_pipeline_run(timestamp1, 5, None)
    run_id2 = db_util.insert_pipeline_run(timestamp2, 10, None)
    
    # Insert governance analysis with risk levels
    gov_dict1 = {
        'risk': 'low',
        'escalation': 'None required',
        'compliance_issues': [],
        'commentary': 'All systems normal'
    }
    
    gov_dict2 = {
        'risk': 'high',
        'escalation': 'Escalate to on-call',
        'compliance_issues': ['Security patch missing'],
        'commentary': 'Critical issues detected'
    }
    
    db_util.insert_governance_analysis(run_id1, gov_dict1)
    db_util.insert_governance_analysis(run_id2, gov_dict2)
    
    # Get risk trend
    result = db_util.get_risk_trend()
    
    # Verify results
    assert isinstance(result, list)
    assert len(result) == 2
    
    # Check first record
    assert result[0]['run_id'] == run_id1
    assert result[0]['risk'] == 'low'
    assert result[0]['timestamp'] == timestamp1
    assert 'date' in result[0]
    assert 'time' in result[0]
    
    # Check second record
    assert result[1]['run_id'] == run_id2
    assert result[1]['risk'] == 'high'
    assert result[1]['timestamp'] == timestamp2
    assert 'date' in result[1]
    assert 'time' in result[1]


def test_get_risk_trend_ordering(temp_db):
    """Test get_risk_trend returns records in chronological order."""
    # Insert test pipeline runs with different timestamps
    timestamp1 = "2025-11-18T10:00:00.000000"
    timestamp2 = "2025-11-18T11:00:00.000000"
    timestamp3 = "2025-11-18T09:00:00.000000"  # Earlier than timestamp1
    
    run_id1 = db_util.insert_pipeline_run(timestamp1, 5, None)
    run_id2 = db_util.insert_pipeline_run(timestamp2, 10, None)
    run_id3 = db_util.insert_pipeline_run(timestamp3, 3, None)
    
    # Insert governance analysis
    gov_dict = {
        'risk': 'medium',
        'escalation': 'Monitor',
        'compliance_issues': [],
        'commentary': 'Test'
    }
    
    db_util.insert_governance_analysis(run_id1, gov_dict)
    db_util.insert_governance_analysis(run_id2, gov_dict)
    db_util.insert_governance_analysis(run_id3, gov_dict)
    
    # Get risk trend
    result = db_util.get_risk_trend()
    
    # Verify chronological ordering (ascending)
    assert len(result) == 3
    assert result[0]['run_id'] == run_id3  # Earliest timestamp
    assert result[1]['run_id'] == run_id1
    assert result[2]['run_id'] == run_id2  # Latest timestamp


def test_get_risk_trend_skips_null_risk(temp_db):
    """Test get_risk_trend skips records with NULL risk values."""
    # Insert test pipeline run
    timestamp = datetime.utcnow().isoformat(timespec="microseconds")
    run_id = db_util.insert_pipeline_run(timestamp, 5, None)
    
    # Insert governance analysis with NULL risk (by manually inserting)
    with db_util.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO governance_analysis (run_id, risk, escalation, commentary)
            VALUES (?, NULL, ?, ?)
        """, (run_id, 'None', 'Test'))
    
    # Get risk trend
    result = db_util.get_risk_trend()
    
    # Should be empty since risk is NULL
    assert len(result) == 0


def test_get_risk_trend_all_risk_levels(temp_db):
    """Test get_risk_trend handles all risk levels correctly."""
    risk_levels = ['low', 'medium', 'high', 'critical']
    
    for i, risk_level in enumerate(risk_levels):
        timestamp = f"2025-11-18T10:{i:02d}:00.000000"
        run_id = db_util.insert_pipeline_run(timestamp, i + 1, None)
        
        gov_dict = {
            'risk': risk_level,
            'escalation': 'Test',
            'compliance_issues': [],
            'commentary': f'Test {risk_level}'
        }
        
        db_util.insert_governance_analysis(run_id, gov_dict)
    
    # Get risk trend
    result = db_util.get_risk_trend()
    
    # Verify all risk levels are present
    assert len(result) == 4
    assert result[0]['risk'] == 'low'
    assert result[1]['risk'] == 'medium'
    assert result[2]['risk'] == 'high'
    assert result[3]['risk'] == 'critical'
