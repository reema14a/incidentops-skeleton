#!/usr/bin/env python3
"""Integration test for GovernanceInsightsAgent in the pipeline."""

import json
from unittest.mock import Mock, patch, MagicMock
from orchestrator.orchestrator import PipelineExecutor


def test_pipeline_with_governance_insights():
    """Test that the pipeline executes successfully with GovernanceInsightsAgent."""
    
    print("\n" + "="*60)
    print("PIPELINE INTEGRATION TEST - WITH GOVERNANCE INSIGHTS")
    print("="*60)
    
    # Mock all agents to return valid data structures
    mock_alerts = [
        {
            'timestamp': '2025-11-16 10:00:00',
            'level': 'ERROR',
            'message': 'Test alert',
            'line_number': 1
        }
    ]
    
    mock_llm_summary_output = {
        'alerts': mock_alerts,
        'llm_summary': {
            'summary': 'Test summary',
            'categories': ['test'],
            'severity_breakdown': {'ERROR': 1},
            'root_causes': ['test cause']
        }
    }
    
    mock_triaged = [
        {
            'timestamp': '2025-11-16 10:00:00',
            'level': 'ERROR',
            'message': 'Test alert',
            'severity': 'high',
            'category': 'test'
        }
    ]
    
    mock_resolution_output = {
        'resolution_plans': [
            {
                'alert_id': '1',
                'severity': 'high',
                'category': 'test',
                'message': 'Test alert',
                'recommended_actions': ['Action 1'],
                'priority': 1,
                'reasoning': 'Test reasoning'
            }
        ],
        'llm_resolution_summary': {
            'summary': 'Test resolution summary',
            'escalation': 'None',
            'affected_systems': []
        }
    }
    
    mock_audit_summary = {
        'status': 'logged',
        'count': 1,
        'timestamp': '2025-11-16 10:00:00',
        'audit_entry': {
            'execution_timestamp': '2025-11-16 10:00:00',
            'total_incidents': 1,
            'stage_outputs': {}
        }
    }
    
    mock_governance_output = {
        'audit_summary': mock_audit_summary,
        'governance_analysis': {
            'risk': 'medium',
            'escalation': 'Monitor',
            'escalation_category': 'monitor',
            'compliance_issues': [],
            'commentary': 'Test commentary'
        }
    }
    
    mock_insights_output = {
        'governance_output': mock_governance_output,
        'insights': {
            'trend_summary': 'Test trend summary',
            'risk_trend': 'Test risk trend',
            'compliance_trend': 'Test compliance trend',
            'recurring_issues': [],
            'category_hotspots': [],
            'recommendations': ['Test recommendation'],
            'anomaly_detection': 'No anomalies detected'
        }
    }
    
    mock_notification_output = {
        'governance_output': mock_governance_output,
        'notification_status': 'skipped',
        'notifications_sent': []
    }
    
    # Mock DB utility functions
    with patch('orchestrator.orchestrator.db_util') as mock_db_util:
        # Mock DB functions
        mock_db_util.insert_pipeline_run.return_value = 1
        mock_db_util.insert_audit_summary.return_value = True
        mock_db_util.insert_governance_analysis.return_value = True
        mock_db_util.insert_compliance_issues.return_value = True
        mock_db_util.insert_insights_history.return_value = True
        mock_db_util.insert_notification_event.return_value = True
        mock_db_util.get_connection.return_value.__enter__ = Mock()
        mock_db_util.get_connection.return_value.__exit__ = Mock()
        
        # Create a mock connection context manager
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_util.get_connection.return_value = MagicMock()
        mock_db_util.get_connection.return_value.__enter__.return_value = mock_conn
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock all agent run methods
        executor.agents['monitor'].run = Mock(return_value=mock_alerts)
        executor.agents['llm_summary'].run = Mock(return_value=mock_llm_summary_output)
        executor.agents['triage'].run = Mock(return_value=mock_triaged)
        executor.agents['llm_resolution'].run = Mock(return_value=mock_resolution_output)
        executor.agents['opslog'].run = Mock(return_value=mock_audit_summary)
        executor.agents['governance'].run = Mock(return_value=mock_governance_output)
        executor.agents['insights'].run = Mock(return_value=mock_insights_output)
        executor.agents['notification'].run = Mock(return_value=mock_notification_output)
        
        # Run pipeline
        result = executor.run()
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'governance_output' in result, "Result must contain 'governance_output'"
    assert 'notification_status' in result, "Result must contain 'notification_status'"
    assert 'notifications_sent' in result, "Result must contain 'notifications_sent'"
    assert 'insights' in result, "Result must contain 'insights'"
    assert 'db_write_status' in result, "Result must contain 'db_write_status'"
    assert 'run_id' in result, "Result must contain 'run_id'"
    print("  ✓ Result has all required fields")
    
    # Verify insights structure
    insights = result['insights']
    assert 'trend_summary' in insights, "Insights must have 'trend_summary'"
    assert 'risk_trend' in insights, "Insights must have 'risk_trend'"
    assert 'compliance_trend' in insights, "Insights must have 'compliance_trend'"
    assert 'recurring_issues' in insights, "Insights must have 'recurring_issues'"
    assert 'category_hotspots' in insights, "Insights must have 'category_hotspots'"
    assert 'recommendations' in insights, "Insights must have 'recommendations'"
    assert 'anomaly_detection' in insights, "Insights must have 'anomaly_detection'"
    print("  ✓ Insights has all required fields")
    
    # Verify DB write status
    db_status = result['db_write_status']
    assert 'insights_history' in db_status, "DB write status must include 'insights_history'"
    print("  ✓ DB write status includes insights_history")
    
    # Verify agent execution order
    executor.agents['monitor'].run.assert_called_once()
    executor.agents['llm_summary'].run.assert_called_once()
    executor.agents['triage'].run.assert_called_once()
    executor.agents['llm_resolution'].run.assert_called_once()
    executor.agents['opslog'].run.assert_called_once()
    executor.agents['governance'].run.assert_called_once()
    executor.agents['insights'].run.assert_called_once()
    executor.agents['notification'].run.assert_called_once()
    print("  ✓ All agents executed in correct order")
    
    # Verify GovernanceInsightsAgent received correct input
    insights_call_args = executor.agents['insights'].run.call_args
    assert insights_call_args[0][0] == mock_governance_output, "GovernanceInsightsAgent should receive governance output"
    print("  ✓ GovernanceInsightsAgent received correct input")
    
    # Verify NotificationAgent received correct input (governance_output from insights)
    notification_call_args = executor.agents['notification'].run.call_args
    assert notification_call_args[0][0] == mock_governance_output, "NotificationAgent should receive governance output"
    print("  ✓ NotificationAgent received correct input")
    
    # Verify DB insert_insights_history was called
    mock_db_util.insert_insights_history.assert_called_once()
    call_args = mock_db_util.insert_insights_history.call_args
    assert call_args[0][0] == 1, "Should use run_id 1"
    assert call_args[0][1] == mock_insights_output['insights'], "Should pass insights data"
    print("  ✓ DB insert_insights_history called correctly")
    
    print("\n" + "="*60)
    print("✓ Pipeline integration test passed successfully")
    print("="*60)
    
    return result


if __name__ == "__main__":
    test_pipeline_with_governance_insights()
    
    print("\n" + "="*60)
    print("ALL INTEGRATION TESTS PASSED ✓")
    print("="*60)
