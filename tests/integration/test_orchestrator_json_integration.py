"""
Integration test to verify orchestrator stores full JSON data in database.
"""
import json
import tempfile
import os
from unittest.mock import patch, MagicMock

# Set up temporary database for testing
temp_db = tempfile.NamedTemporaryFile(mode='w', suffix='.db', delete=False)
temp_db_path = temp_db.name
temp_db.close()

# Configure settings to use temp database
os.environ['DATABASE_PATH'] = temp_db_path

# Import after setting environment
from orchestrator.orchestrator import PipelineExecutor
from db import db_util


def test_orchestrator_stores_full_audit_json():
    """Test that orchestrator stores complete audit_dict as JSON."""
    print("\n=== Testing Orchestrator Audit JSON Storage ===")
    
    # Mock all agents to return controlled data
    with patch('orchestrator.orchestrator.MonitorAgent') as MockMonitor, \
         patch('orchestrator.orchestrator.LLMAlertSummaryAgent') as MockLLMSummary, \
         patch('orchestrator.orchestrator.TriageAgent') as MockTriage, \
         patch('orchestrator.orchestrator.LLMResolutionAgent') as MockLLMResolution, \
         patch('orchestrator.orchestrator.OpsLogAgent') as MockOpsLog, \
         patch('orchestrator.orchestrator.LLMGovernanceAgent') as MockGovernance, \
         patch('orchestrator.orchestrator.NotificationAgent') as MockNotification:
        
        # Setup mock returns
        mock_alerts = [
            {"timestamp": "2025-11-18T10:00:00", "level": "ERROR", "message": "Test alert"}
        ]
        
        mock_llm_summary_output = {
            "alerts": mock_alerts,
            "llm_summary": {"summary": "Test summary"}
        }
        
        mock_triaged = [
            {"timestamp": "2025-11-18T10:00:00", "level": "ERROR", "message": "Test alert", 
             "severity": "high", "category": "security"}
        ]
        
        mock_resolution_output = {
            "resolution_plans": mock_triaged,
            "llm_resolution_summary": {"summary": "Resolution summary"}
        }
        
        # OpsLog returns audit dict with extra fields
        mock_audit_dict = {
            "status": "completed",
            "count": 1,
            "timestamp": "2025-11-18T10:00:00",
            "extra_field": "extra_value",
            "nested_data": {"key": "value"},
            "list_data": [1, 2, 3]
        }
        
        mock_governance_output = {
            "audit_summary": mock_audit_dict,
            "governance_analysis": {
                "risk": "medium",
                "escalation": "required",
                "commentary": "Test commentary",
                "compliance_issues": ["Issue 1"]
            }
        }
        
        mock_notification_output = {
            "governance_output": mock_governance_output,
            "notification_status": "success",
            "notifications_sent": []
        }
        
        # Configure mocks
        MockMonitor.return_value.run.return_value = mock_alerts
        MockLLMSummary.return_value.run.return_value = mock_llm_summary_output
        MockTriage.return_value.run.return_value = mock_triaged
        MockLLMResolution.return_value.run.return_value = mock_resolution_output
        MockOpsLog.return_value.run.return_value = mock_audit_dict
        MockGovernance.return_value.run.return_value = mock_governance_output
        MockNotification.return_value.run.return_value = mock_notification_output
        
        # Run pipeline
        executor = PipelineExecutor()
        result = executor.run()
        
        print(f"Pipeline run_id: {executor.run_id}")
        assert executor.run_id is not None
        
        # Verify audit_data JSON was stored
        with db_util.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT audit_data FROM audit_summary WHERE run_id = ?", (executor.run_id,))
            row = cursor.fetchone()
            
            assert row is not None, "No audit_summary row found"
            assert row['audit_data'] is not None, "audit_data column is NULL"
            
            stored_audit = json.loads(row['audit_data'])
            print(f"Stored audit_data: {stored_audit}")
            
            # Verify all fields including extra ones
            assert stored_audit == mock_audit_dict
            assert stored_audit['extra_field'] == "extra_value"
            assert stored_audit['nested_data'] == {"key": "value"}
            assert stored_audit['list_data'] == [1, 2, 3]
            print("✓ Full audit_dict stored correctly in JSON")


def test_orchestrator_stores_full_governance_json():
    """Test that orchestrator stores complete gov_dict as JSON."""
    print("\n=== Testing Orchestrator Governance JSON Storage ===")
    
    # Mock all agents to return controlled data
    with patch('orchestrator.orchestrator.MonitorAgent') as MockMonitor, \
         patch('orchestrator.orchestrator.LLMAlertSummaryAgent') as MockLLMSummary, \
         patch('orchestrator.orchestrator.TriageAgent') as MockTriage, \
         patch('orchestrator.orchestrator.LLMResolutionAgent') as MockLLMResolution, \
         patch('orchestrator.orchestrator.OpsLogAgent') as MockOpsLog, \
         patch('orchestrator.orchestrator.LLMGovernanceAgent') as MockGovernance, \
         patch('orchestrator.orchestrator.NotificationAgent') as MockNotification:
        
        # Setup mock returns
        mock_alerts = [
            {"timestamp": "2025-11-18T10:00:00", "level": "ERROR", "message": "Test alert"}
        ]
        
        mock_llm_summary_output = {
            "alerts": mock_alerts,
            "llm_summary": {"summary": "Test summary"}
        }
        
        mock_triaged = [
            {"timestamp": "2025-11-18T10:00:00", "level": "ERROR", "message": "Test alert", 
             "severity": "high", "category": "security"}
        ]
        
        mock_resolution_output = {
            "resolution_plans": mock_triaged,
            "llm_resolution_summary": {"summary": "Resolution summary"}
        }
        
        mock_audit_dict = {
            "status": "completed",
            "count": 1,
            "timestamp": "2025-11-18T10:00:00"
        }
        
        # Governance returns dict with extra fields
        mock_gov_dict = {
            "risk": "high",
            "escalation": "immediate",
            "commentary": "Critical issues",
            "compliance_issues": ["Issue 1", "Issue 2"],
            "extra_metadata": {"analyst": "Jane Doe", "reviewed": True},
            "risk_score": 95,
            "additional_context": {"source": "automated", "confidence": 0.98}
        }
        
        mock_governance_output = {
            "audit_summary": mock_audit_dict,
            "governance_analysis": mock_gov_dict
        }
        
        mock_notification_output = {
            "governance_output": mock_governance_output,
            "notification_status": "success",
            "notifications_sent": []
        }
        
        # Configure mocks
        MockMonitor.return_value.run.return_value = mock_alerts
        MockLLMSummary.return_value.run.return_value = mock_llm_summary_output
        MockTriage.return_value.run.return_value = mock_triaged
        MockLLMResolution.return_value.run.return_value = mock_resolution_output
        MockOpsLog.return_value.run.return_value = mock_audit_dict
        MockGovernance.return_value.run.return_value = mock_governance_output
        MockNotification.return_value.run.return_value = mock_notification_output
        
        # Run pipeline
        executor = PipelineExecutor()
        result = executor.run()
        
        print(f"Pipeline run_id: {executor.run_id}")
        assert executor.run_id is not None
        
        # Verify governance_data JSON was stored
        with db_util.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT governance_data FROM governance_analysis WHERE run_id = ?", (executor.run_id,))
            row = cursor.fetchone()
            
            assert row is not None, "No governance_analysis row found"
            assert row['governance_data'] is not None, "governance_data column is NULL"
            
            stored_gov = json.loads(row['governance_data'])
            print(f"Stored governance_data: {stored_gov}")
            
            # Verify all fields including extra ones
            assert stored_gov == mock_gov_dict
            assert stored_gov['extra_metadata'] == {"analyst": "Jane Doe", "reviewed": True}
            assert stored_gov['risk_score'] == 95
            assert stored_gov['additional_context'] == {"source": "automated", "confidence": 0.98}
            print("✓ Full gov_dict stored correctly in JSON")


if __name__ == "__main__":
    try:
        test_orchestrator_stores_full_audit_json()
        test_orchestrator_stores_full_governance_json()
        print("\n✅ All orchestrator JSON integration tests passed!")
    finally:
        # Clean up temp database
        if os.path.exists(temp_db_path):
            os.unlink(temp_db_path)
            print(f"\nCleaned up temporary database: {temp_db_path}")
