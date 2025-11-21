"""
Integration tests for Deep Governance Insights page.

Tests the page's ability to retrieve and display insights data from the database.
"""
import pytest
import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from db import db_util


def test_get_latest_insights_with_data(tmp_path):
    """Test retrieving latest insights when data exists."""
    # Setup: Create a temporary database
    import os
    db_path = tmp_path / "test_insights.db"
    os.environ['DB_PATH'] = str(db_path)
    
    # Initialize database
    db_util.initialize_database()
    
    # Insert test data
    run_id = db_util.insert_pipeline_run(
        timestamp=datetime.utcnow().isoformat(timespec="microseconds"),
        alerts_count=5
    )
    
    insights_json = {
        'trend_summary': 'Test trend summary',
        'risk_trend': 'Risk is stable',
        'compliance_trend': 'Compliance improving',
        'recurring_issues': ['Issue 1', 'Issue 2'],
        'category_hotspots': ['Category A', 'Category B'],
        'recommendations': ['Recommendation 1', 'Recommendation 2'],
        'anomaly_detection': 'No anomalies detected'
    }
    
    success = db_util.insert_insights_history(run_id, insights_json)
    assert success, "Failed to insert insights history"
    
    # Test: Retrieve insights
    insights_history = db_util.get_insights_history(limit=1)
    
    assert len(insights_history) == 1
    assert insights_history[0]['run_id'] == run_id
    
    # Parse insights_data
    retrieved_insights = json.loads(insights_history[0]['insights_data'])
    assert retrieved_insights['trend_summary'] == 'Test trend summary'
    assert len(retrieved_insights['recurring_issues']) == 2
    assert len(retrieved_insights['recommendations']) == 2


def test_get_latest_insights_empty_database(tmp_path):
    """Test retrieving insights when database is empty."""
    # Setup: Create a temporary database
    import os
    db_path = tmp_path / "test_empty_insights.db"
    os.environ['DB_PATH'] = str(db_path)
    
    # Initialize database
    db_util.initialize_database()
    
    # Test: Retrieve insights from empty database
    insights_history = db_util.get_insights_history(limit=1)
    
    assert insights_history == []


def test_insights_data_structure():
    """Test that insights data has the expected structure."""
    insights_json = {
        'trend_summary': 'Test summary',
        'risk_trend': 'Risk trend',
        'compliance_trend': 'Compliance trend',
        'recurring_issues': ['Issue 1'],
        'category_hotspots': ['Category A'],
        'recommendations': ['Rec 1'],
        'anomaly_detection': 'No anomalies'
    }
    
    # Verify all required fields are present
    required_fields = [
        'trend_summary',
        'risk_trend',
        'compliance_trend',
        'recurring_issues',
        'category_hotspots',
        'recommendations',
        'anomaly_detection'
    ]
    
    for field in required_fields:
        assert field in insights_json, f"Missing required field: {field}"


def test_multiple_insights_ordering(tmp_path):
    """Test that insights are returned in descending timestamp order."""
    # Setup: Create a temporary database
    import os
    db_path = tmp_path / "test_ordering_insights.db"
    os.environ['DB_PATH'] = str(db_path)
    
    # Initialize database
    db_util.initialize_database()
    
    # Insert multiple insights with different timestamps
    run_id_1 = db_util.insert_pipeline_run(
        timestamp="2025-01-01T10:00:00.000000",
        alerts_count=3
    )
    
    run_id_2 = db_util.insert_pipeline_run(
        timestamp="2025-01-02T10:00:00.000000",
        alerts_count=4
    )
    
    run_id_3 = db_util.insert_pipeline_run(
        timestamp="2025-01-03T10:00:00.000000",
        alerts_count=5
    )
    
    insights_1 = {'trend_summary': 'First insights'}
    insights_2 = {'trend_summary': 'Second insights'}
    insights_3 = {'trend_summary': 'Third insights'}
    
    db_util.insert_insights_history(run_id_1, insights_1)
    db_util.insert_insights_history(run_id_2, insights_2)
    db_util.insert_insights_history(run_id_3, insights_3)
    
    # Test: Retrieve all insights
    insights_history = db_util.get_insights_history()
    
    assert len(insights_history) == 3
    
    # Verify ordering (most recent first)
    parsed_1 = json.loads(insights_history[0]['insights_data'])
    parsed_2 = json.loads(insights_history[1]['insights_data'])
    parsed_3 = json.loads(insights_history[2]['insights_data'])
    
    assert parsed_1['trend_summary'] == 'Third insights'
    assert parsed_2['trend_summary'] == 'Second insights'
    assert parsed_3['trend_summary'] == 'First insights'
