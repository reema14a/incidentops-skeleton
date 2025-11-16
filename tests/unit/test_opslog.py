#!/usr/bin/env python3
"""Test to verify OpsLogAgent implementation."""

import json
import os
from unittest.mock import Mock, patch
from agents.monitor_agent import MonitorAgent
from agents.triage_agent import TriageAgent
from agents.llm_resolution_agent import LLMResolutionAgent
from agents.opslog_agent import OpsLogAgent

def test_opslog_agent():
    """Test the OpsLogAgent with mocked LLMResolutionAgent output."""
    
    # Step 1: Run monitor and triage to get triaged alerts
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    triage = TriageAgent("Triage")
    triaged_alerts = triage.run(alerts)
    
    # Step 2: Mock LLMResolutionAgent to get resolution plans
    mock_llm_response = {
        'resolution_plans': [
            {
                'alert_id': f"{alert.get('timestamp', 'unknown')}_{idx}",
                'timestamp': alert.get('timestamp'),
                'severity': alert.get('severity'),
                'category': alert.get('category'),
                'message': alert.get('message'),
                'recommended_actions': [
                    f"Investigate {alert.get('category')} issue",
                    "Review system logs",
                    "Monitor metrics"
                ],
                'priority': {'critical': 1, 'high': 2, 'medium': 3, 'low': 4}.get(alert.get('severity'), 3),
                'reasoning': f"Standard response for {alert.get('severity')} severity"
            }
            for idx, alert in enumerate(triaged_alerts)
        ],
        'llm_resolution_summary': {
            'summary': 'Test resolution summary',
            'escalation': 'Test escalation',
            'affected_systems': ['test']
        }
    }
    
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        resolution = LLMResolutionAgent("Resolution")
        resolution.run = Mock(return_value=mock_llm_response)
        resolution_output = resolution.run(triaged_alerts)
    
    resolution_plans = resolution_output['resolution_plans']
    
    print("\n" + "="*60)
    print("RESOLUTION PLANS INPUT:")
    print("="*60)
    for plan in resolution_plans:
        print(f"  [{plan['severity'].upper()}] [{plan['category'].upper()}] Priority {plan['priority']}")
        print(f"    {plan['message']}")
    
    # Step 2: Run OpsLogAgent to generate audit log
    print("\n" + "="*60)
    print("OPSLOG PROCESSING:")
    print("="*60)
    
    # Use a test output path
    test_output_path = "data/test_output_log.json"
    opslog = OpsLogAgent("OpsLog", output_path=test_output_path)
    summary = opslog.run(resolution_plans)
    
    # Step 3: Verify summary
    print("\n" + "="*60)
    print("OPERATION SUMMARY:")
    print("="*60)
    print(f"  Status: {summary['status']}")
    print(f"  Count: {summary['count']}")
    print(f"  Timestamp: {summary['timestamp']}")
    print(f"  Output Path: {summary['output_path']}")
    
    # Verify summary fields
    assert summary['status'] == 'logged', "Status should be 'logged'"
    assert summary['count'] == len(resolution_plans), "Count mismatch"
    assert 'timestamp' in summary, "Missing timestamp"
    assert summary['output_path'] == test_output_path, "Output path mismatch"
    
    print("\n  ✓ Summary fields validated")
    
    # Step 4: Verify audit log file was created
    print("\n" + "="*60)
    print("AUDIT LOG FILE VERIFICATION:")
    print("="*60)
    
    assert os.path.exists(test_output_path), "Audit log file not created"
    print(f"  ✓ File created at {test_output_path}")
    
    # Step 5: Verify audit log structure
    with open(test_output_path, 'r') as f:
        audit_logs = json.load(f)
    
    assert isinstance(audit_logs, list), "Audit logs should be a list"
    assert len(audit_logs) > 0, "Audit logs should not be empty"
    
    audit_entry = audit_logs[-1]  # Get the latest entry
    
    # Verify required top-level fields (factual data only)
    required_fields = [
        'execution_timestamp',
        'pipeline_name',
        'agent_execution_order',
        'stage_outputs',
        'resolution_plans',
        'total_incidents',
        'audit_metadata'
    ]
    
    for field in required_fields:
        assert field in audit_entry, f"Missing required field: {field}"
        print(f"  ✓ Field present: {field}")
    
    # Verify recommendations_summary is NOT present (moved to LLMGovernanceAgent)
    assert 'recommendations_summary' not in audit_entry, "recommendations_summary should not be in OpsLogAgent output (belongs in LLMGovernanceAgent)"
    print("  ✓ recommendations_summary correctly absent (interpretive logic moved to LLMGovernanceAgent)")
    
    # Verify agent execution order
    expected_order = ["MonitorAgent", "TriageAgent", "LLMResolutionAgent", "OpsLogAgent"]
    assert audit_entry['agent_execution_order'] == expected_order, "Agent execution order mismatch"
    print(f"  ✓ Agent execution order correct: {expected_order}")
    
    # Verify stage outputs structure
    stage_outputs = audit_entry['stage_outputs']
    assert 'monitor_stage' in stage_outputs, "Missing monitor_stage"
    assert 'triage_stage' in stage_outputs, "Missing triage_stage"
    assert 'resolution_stage' in stage_outputs, "Missing resolution_stage"
    print("  ✓ All stage outputs present")
    
    # Verify monitor stage
    monitor_stage = stage_outputs['monitor_stage']
    assert 'alerts_detected' in monitor_stage, "Missing alerts_detected"
    assert 'alert_ids' in monitor_stage, "Missing alert_ids"
    assert monitor_stage['alerts_detected'] == len(resolution_plans), "Alert count mismatch"
    print(f"  ✓ Monitor stage: {monitor_stage['alerts_detected']} alerts")
    
    # Verify triage stage
    triage_stage = stage_outputs['triage_stage']
    assert 'severity_distribution' in triage_stage, "Missing severity_distribution"
    assert 'category_distribution' in triage_stage, "Missing category_distribution"
    print(f"  ✓ Triage stage: severity and category distributions present")
    
    # Verify resolution stage
    resolution_stage = stage_outputs['resolution_stage']
    assert 'plans_generated' in resolution_stage, "Missing plans_generated"
    assert 'priority_distribution' in resolution_stage, "Missing priority_distribution"
    assert resolution_stage['plans_generated'] == len(resolution_plans), "Plans count mismatch"
    print(f"  ✓ Resolution stage: {resolution_stage['plans_generated']} plans")
    
    # Verify audit metadata
    metadata = audit_entry['audit_metadata']
    assert 'logged_by' in metadata, "Missing logged_by"
    assert 'log_version' in metadata, "Missing log_version"
    assert 'entry_id' in metadata, "Missing entry_id"
    assert metadata['logged_by'] == "OpsLog", "Incorrect logged_by value"
    print(f"  ✓ Audit metadata: logged by {metadata['logged_by']}")
    
    # Verify resolution plans are included
    assert len(audit_entry['resolution_plans']) == len(resolution_plans), "Resolution plans count mismatch"
    print(f"  ✓ All {len(resolution_plans)} resolution plans included")
    
    # Verify total incidents
    assert audit_entry['total_incidents'] == len(resolution_plans), "Total incidents mismatch"
    print(f"  ✓ Total incidents: {audit_entry['total_incidents']}")
    
    print("\n" + "="*60)
    print("✓ All OpsLogAgent tests passed successfully")
    print("="*60)
    
    # Clean up test file
    if os.path.exists(test_output_path):
        os.remove(test_output_path)
        print(f"\n✓ Test file cleaned up: {test_output_path}")
    
    return summary

def test_opslog_agent_empty_input():
    """Test OpsLogAgent behavior with empty input."""
    
    print("\n" + "="*60)
    print("OPSLOG AGENT TEST - EMPTY INPUT")
    print("="*60)
    
    test_output_path = "data/test_empty_log.json"
    opslog = OpsLogAgent("OpsLog", output_path=test_output_path)
    summary = opslog.run([])
    
    # Should handle empty input gracefully
    assert summary['status'] == 'no_data', "Status should be 'no_data' for empty input"
    assert summary['count'] == 0, "Count should be 0"
    assert summary['output_path'] is None, "Output path should be None for no data"
    
    print("  ✓ Handles empty input gracefully")
    print(f"  ✓ Status: {summary['status']}")
    print(f"  ✓ Count: {summary['count']}")
    
    print("\n" + "="*60)
    print("✓ Empty input test passed")
    print("="*60)
    
    return summary

if __name__ == "__main__":
    # Run all tests
    test_opslog_agent()
    test_opslog_agent_empty_input()
    
    print("\n" + "="*60)
    print("ALL OPSLOG AGENT TESTS PASSED ✓")
    print("="*60)
