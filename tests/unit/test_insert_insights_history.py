"""
Unit tests for insert_insights_history function.
"""

import os
import tempfile
import pytest
import json

from db.db_util import (
    initialize_database,
    get_connection,
    insert_pipeline_run,
    insert_insights_history
)


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


def test_insert_insights_history_success(temp_db):
    """Test successful insertion of insights history."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run first
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    
    assert run_id is not None, "Pipeline run should be created"
    
    # Insert insights history
    insights_data = {
        "summary": "System stability improving",
        "trends": ["Decreasing incident count", "Improved response times"],
        "recommendations": ["Continue monitoring", "Review automation rules"]
    }
    
    success = insert_insights_history(run_id, insights_data)
    
    assert success is True, "Insertion should succeed"
    
    # Verify the data was inserted correctly
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT run_id, insights_data, timestamp
            FROM insights_history
            WHERE run_id = ?
        """, (run_id,))
        
        result = cursor.fetchone()
        
        assert result is not None, "Record should exist"
        assert result['run_id'] == run_id
        
        # Parse and verify JSON data
        stored_insights = json.loads(result['insights_data'])
        assert stored_insights == insights_data
        
        # Verify timestamp is set
        assert result['timestamp'] is not None
        assert 'T' in result['timestamp'], "Timestamp should be in ISO 8601 format"


def test_insert_insights_history_complex_data(temp_db):
    """Test insertion of complex insights data with nested structures."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run first
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T11:00:00.000000',
        alerts_count=3
    )
    
    # Insert complex insights history
    insights_data = {
        "summary": "Comprehensive analysis",
        "trends": [
            {"metric": "incident_count", "direction": "decreasing", "percentage": -15.5},
            {"metric": "response_time", "direction": "improving", "percentage": 10.2}
        ],
        "recommendations": [
            {
                "priority": "high",
                "action": "Review automation rules",
                "reason": "Multiple false positives detected"
            },
            {
                "priority": "medium",
                "action": "Update monitoring thresholds",
                "reason": "Current thresholds may be too sensitive"
            }
        ],
        "metadata": {
            "analysis_version": "1.0",
            "confidence_score": 0.85
        }
    }
    
    success = insert_insights_history(run_id, insights_data)
    
    assert success is True, "Insertion should succeed"
    
    # Verify the complex data was stored correctly
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT insights_data
            FROM insights_history
            WHERE run_id = ?
        """, (run_id,))
        
        result = cursor.fetchone()
        stored_insights = json.loads(result['insights_data'])
        
        # Verify nested structures
        assert stored_insights == insights_data
        assert len(stored_insights['trends']) == 2
        assert stored_insights['trends'][0]['percentage'] == -15.5
        assert stored_insights['recommendations'][0]['priority'] == 'high'
        assert stored_insights['metadata']['confidence_score'] == 0.85


def test_insert_insights_history_multiple_records(temp_db):
    """Test inserting multiple insights records for different runs."""
    os.environ['DB_PATH'] = temp_db
    
    # Create multiple pipeline runs
    run_id_1 = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    run_id_2 = insert_pipeline_run(
        timestamp='2025-11-19T11:00:00.000000',
        alerts_count=3
    )
    
    # Insert insights for both runs
    insights_1 = {"summary": "First run insights", "trends": ["trend1"]}
    insights_2 = {"summary": "Second run insights", "trends": ["trend2"]}
    
    success_1 = insert_insights_history(run_id_1, insights_1)
    success_2 = insert_insights_history(run_id_2, insights_2)
    
    assert success_1 is True
    assert success_2 is True
    
    # Verify both records exist
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM insights_history")
        result = cursor.fetchone()
        
        assert result['count'] == 2, "Should have 2 insights records"


def test_insert_insights_history_invalid_run_id(temp_db):
    """Test insertion with invalid run_id (foreign key constraint)."""
    os.environ['DB_PATH'] = temp_db
    
    # Try to insert insights for non-existent run_id
    insights_data = {"summary": "Test insights"}
    
    # This should fail due to foreign key constraint
    success = insert_insights_history(999999, insights_data)
    
    assert success is False, "Insertion should fail for invalid run_id"


def test_insert_insights_history_empty_dict(temp_db):
    """Test insertion with empty insights dictionary."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run first
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=0
    )
    
    # Insert empty insights
    insights_data = {}
    
    success = insert_insights_history(run_id, insights_data)
    
    assert success is True, "Insertion should succeed even with empty dict"
    
    # Verify the data was stored
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT insights_data
            FROM insights_history
            WHERE run_id = ?
        """, (run_id,))
        
        result = cursor.fetchone()
        stored_insights = json.loads(result['insights_data'])
        
        assert stored_insights == {}
