"""
Unit tests for get_insights_history function.
"""

import os
import tempfile
import pytest
import json

from db.db_util import (
    initialize_database,
    get_connection,
    insert_pipeline_run,
    insert_insights_history,
    get_insights_history
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


def test_get_insights_history_empty_database(temp_db):
    """Test retrieving insights history from empty database."""
    os.environ['DB_PATH'] = temp_db
    
    results = get_insights_history()
    
    assert results == [], "Should return empty list for empty database"


def test_get_insights_history_single_record(temp_db):
    """Test retrieving a single insights history record."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run and insert insights
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    
    insights_data = {
        "summary": "System stability improving",
        "trends": ["Decreasing incident count"],
        "recommendations": ["Continue monitoring"]
    }
    
    insert_insights_history(run_id, insights_data)
    
    # Retrieve insights history
    results = get_insights_history()
    
    assert len(results) == 1, "Should return 1 record"
    
    record = results[0]
    assert 'id' in record
    assert record['run_id'] == run_id
    assert 'insights_data' in record
    assert 'timestamp' in record
    
    # Verify JSON data
    stored_insights = json.loads(record['insights_data'])
    assert stored_insights == insights_data


def test_get_insights_history_multiple_records(temp_db):
    """Test retrieving multiple insights history records."""
    os.environ['DB_PATH'] = temp_db
    
    # Create multiple pipeline runs and insert insights
    run_id_1 = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    run_id_2 = insert_pipeline_run(
        timestamp='2025-11-19T11:00:00.000000',
        alerts_count=3
    )
    run_id_3 = insert_pipeline_run(
        timestamp='2025-11-19T12:00:00.000000',
        alerts_count=2
    )
    
    insights_1 = {"summary": "First insights", "trends": ["trend1"]}
    insights_2 = {"summary": "Second insights", "trends": ["trend2"]}
    insights_3 = {"summary": "Third insights", "trends": ["trend3"]}
    
    insert_insights_history(run_id_1, insights_1)
    insert_insights_history(run_id_2, insights_2)
    insert_insights_history(run_id_3, insights_3)
    
    # Retrieve all insights history
    results = get_insights_history()
    
    assert len(results) == 3, "Should return 3 records"
    
    # Verify records are ordered by timestamp descending (most recent first)
    assert results[0]['run_id'] == run_id_3, "Most recent should be first"
    assert results[1]['run_id'] == run_id_2
    assert results[2]['run_id'] == run_id_1, "Oldest should be last"


def test_get_insights_history_with_limit(temp_db):
    """Test retrieving insights history with limit parameter."""
    os.environ['DB_PATH'] = temp_db
    
    # Create multiple pipeline runs and insert insights
    for i in range(5):
        run_id = insert_pipeline_run(
            timestamp=f'2025-11-19T{10+i}:00:00.000000',
            alerts_count=i
        )
        insights = {"summary": f"Insights {i}", "run": i}
        insert_insights_history(run_id, insights)
    
    # Retrieve with limit
    results = get_insights_history(limit=3)
    
    assert len(results) == 3, "Should return exactly 3 records"
    
    # Verify we got the most recent 3
    for i, record in enumerate(results):
        stored_insights = json.loads(record['insights_data'])
        # Most recent first, so run numbers should be 4, 3, 2
        assert stored_insights['run'] == 4 - i


def test_get_insights_history_limit_zero(temp_db):
    """Test retrieving insights history with limit=0."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run and insert insights
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    insert_insights_history(run_id, {"summary": "Test"})
    
    # Retrieve with limit=0
    results = get_insights_history(limit=0)
    
    assert results == [], "Should return empty list with limit=0"


def test_get_insights_history_limit_exceeds_records(temp_db):
    """Test retrieving insights history when limit exceeds available records."""
    os.environ['DB_PATH'] = temp_db
    
    # Create 2 pipeline runs and insert insights
    for i in range(2):
        run_id = insert_pipeline_run(
            timestamp=f'2025-11-19T{10+i}:00:00.000000',
            alerts_count=i
        )
        insights = {"summary": f"Insights {i}"}
        insert_insights_history(run_id, insights)
    
    # Retrieve with limit=10 (more than available)
    results = get_insights_history(limit=10)
    
    assert len(results) == 2, "Should return all available records (2)"


def test_get_insights_history_complex_data(temp_db):
    """Test retrieving insights history with complex nested data."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run and insert complex insights
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    
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
            }
        ],
        "metadata": {
            "analysis_version": "1.0",
            "confidence_score": 0.85
        }
    }
    
    insert_insights_history(run_id, insights_data)
    
    # Retrieve insights history
    results = get_insights_history()
    
    assert len(results) == 1
    
    # Verify complex data is preserved
    stored_insights = json.loads(results[0]['insights_data'])
    assert stored_insights == insights_data
    assert stored_insights['trends'][0]['percentage'] == -15.5
    assert stored_insights['metadata']['confidence_score'] == 0.85


def test_get_insights_history_timestamp_format(temp_db):
    """Test that timestamps are in correct ISO 8601 format."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run and insert insights
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    
    insights_data = {"summary": "Test insights"}
    insert_insights_history(run_id, insights_data)
    
    # Retrieve insights history
    results = get_insights_history()
    
    assert len(results) == 1
    
    timestamp = results[0]['timestamp']
    
    # Verify ISO 8601 format with microseconds
    assert 'T' in timestamp, "Timestamp should contain 'T' separator"
    assert '.' in timestamp, "Timestamp should contain microseconds"
    
    # Verify it can be parsed
    from datetime import datetime
    dt = datetime.fromisoformat(timestamp)
    assert dt is not None, "Timestamp should be valid ISO 8601 format"


def test_get_insights_history_ordering(temp_db):
    """Test that insights history is ordered by timestamp descending."""
    os.environ['DB_PATH'] = temp_db
    
    # Create pipeline runs with different timestamps
    # Insert them in a specific order to test ordering
    timestamps = [
        '2025-11-19T10:00:00.000000',
        '2025-11-19T12:00:00.000000',
        '2025-11-19T11:00:00.000000',
        '2025-11-19T13:00:00.000000'
    ]
    
    run_ids = []
    for i, ts in enumerate(timestamps):
        run_id = insert_pipeline_run(timestamp=ts, alerts_count=1)
        run_ids.append(run_id)
        insert_insights_history(run_id, {"run_number": i, "pipeline_timestamp": ts})
    
    # Retrieve insights history
    results = get_insights_history()
    
    assert len(results) == 4
    
    # Verify ordering by checking that timestamps are in descending order
    # (most recent insertion first)
    timestamps_retrieved = [record['timestamp'] for record in results]
    
    # Check that each timestamp is greater than or equal to the next one
    for i in range(len(timestamps_retrieved) - 1):
        assert timestamps_retrieved[i] >= timestamps_retrieved[i + 1], \
            f"Timestamps should be in descending order: {timestamps_retrieved[i]} should be >= {timestamps_retrieved[i + 1]}"
    
    # The most recently inserted record should be first (run_number 3)
    first_insights = json.loads(results[0]['insights_data'])
    assert first_insights['run_number'] == 3, "Most recently inserted insights should be first"


def test_get_insights_history_all_fields_present(temp_db):
    """Test that all expected fields are present in returned records."""
    os.environ['DB_PATH'] = temp_db
    
    # Create a pipeline run and insert insights
    run_id = insert_pipeline_run(
        timestamp='2025-11-19T10:00:00.000000',
        alerts_count=5
    )
    
    insights_data = {"summary": "Test insights"}
    insert_insights_history(run_id, insights_data)
    
    # Retrieve insights history
    results = get_insights_history()
    
    assert len(results) == 1
    
    record = results[0]
    
    # Verify all expected fields are present
    expected_fields = ['id', 'run_id', 'insights_data', 'timestamp']
    for field in expected_fields:
        assert field in record, f"Field '{field}' should be present in record"
    
    # Verify field types
    assert isinstance(record['id'], int)
    assert isinstance(record['run_id'], int)
    assert isinstance(record['insights_data'], str)
    assert isinstance(record['timestamp'], str)
