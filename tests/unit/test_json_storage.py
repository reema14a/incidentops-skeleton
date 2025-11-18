"""
Temporary test to verify JSON storage in audit_summary and governance_analysis tables.
"""
import json
import tempfile
import os
from pathlib import Path

# Set up temporary database for testing
temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
temp_db_path = temp_db.name
temp_db.close()

# Configure settings to use temp database
os.environ['DATABASE_PATH'] = temp_db_path

# Import after setting environment
from db import db_util


def test_audit_summary_json_storage():
    """Test that full audit_dict is stored as JSON in audit_data column."""
    print("\n=== Testing audit_summary JSON storage ===")
    
    # Create a pipeline run
    run_id = db_util.insert_pipeline_run("2025-11-18T10:30:00", 5, "test_data.txt")
    print(f"Created pipeline run with ID: {run_id}")
    
    # Create audit dict with extra fields beyond the basic columns
    audit_dict = {
        "status": "completed",
        "count": 5,
        "timestamp": "2025-11-18T10:30:00",
        "extra_field_1": "some_value",
        "extra_field_2": {"nested": "data"},
        "extra_field_3": [1, 2, 3]
    }
    
    # Insert audit summary
    success = db_util.insert_audit_summary(run_id, audit_dict)
    print(f"Insert audit_summary success: {success}")
    assert success is True
    
    # Verify the JSON data was stored
    with db_util.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT audit_data FROM audit_summary WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        
        assert row is not None, "No audit_summary row found"
        assert row['audit_data'] is not None, "audit_data column is NULL"
        
        # Parse the JSON
        stored_data = json.loads(row['audit_data'])
        print(f"Stored audit_data: {stored_data}")
        
        # Verify all fields are present
        assert stored_data == audit_dict, f"Stored data doesn't match: {stored_data} != {audit_dict}"
        print("✓ All audit_dict fields stored correctly in JSON")


def test_governance_analysis_json_storage():
    """Test that full gov_dict is stored as JSON in governance_data column."""
    print("\n=== Testing governance_analysis JSON storage ===")
    
    # Create a pipeline run
    run_id = db_util.insert_pipeline_run("2025-11-18T11:00:00", 3, "test_data2.txt")
    print(f"Created pipeline run with ID: {run_id}")
    
    # Create governance dict with extra fields beyond the basic columns
    gov_dict = {
        "risk": "high",
        "escalation": "immediate",
        "commentary": "Critical issues detected",
        "compliance_issues": ["Issue 1", "Issue 2"],
        "extra_metadata": {"analyst": "John Doe", "reviewed": True},
        "score": 85
    }
    
    # Insert governance analysis
    success = db_util.insert_governance_analysis(run_id, gov_dict)
    print(f"Insert governance_analysis success: {success}")
    assert success is True
    
    # Verify the JSON data was stored
    with db_util.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT governance_data FROM governance_analysis WHERE run_id = ?", (run_id,))
        row = cursor.fetchone()
        
        assert row is not None, "No governance_analysis row found"
        assert row['governance_data'] is not None, "governance_data column is NULL"
        
        # Parse the JSON
        stored_data = json.loads(row['governance_data'])
        print(f"Stored governance_data: {stored_data}")
        
        # Verify all fields are present
        assert stored_data == gov_dict, f"Stored data doesn't match: {stored_data} != {gov_dict}"
        print("✓ All gov_dict fields stored correctly in JSON")


if __name__ == "__main__":
    try:
        test_audit_summary_json_storage()
        test_governance_analysis_json_storage()
        print("\n✅ All JSON storage tests passed!")
    finally:
        # Clean up temp database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
            print(f"\nCleaned up temporary database: {temp_db_path}")
