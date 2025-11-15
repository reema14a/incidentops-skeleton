#!/usr/bin/env python3
"""Integration test for MonitorAgent -> LLMAlertSummaryAgent flow."""

from unittest.mock import Mock, patch
import json
from agents.monitor_agent import MonitorAgent
from agents.llm_alert_summary_agent import LLMAlertSummaryAgent


def test_monitor_to_llm_summary_integration():
    """Test the flow from MonitorAgent to LLMAlertSummaryAgent."""
    
    print("\n" + "="*60)
    print("MONITOR -> LLM SUMMARY INTEGRATION TEST")
    print("="*60)
    
    # Step 1: Run MonitorAgent
    print("\nStep 1: Running MonitorAgent...")
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    print(f"  ✓ MonitorAgent detected {len(alerts)} alerts")
    
    # Step 2: Pass alerts to LLMAlertSummaryAgent
    print("\nStep 2: Running LLMAlertSummaryAgent...")
    
    # Mock LLM response
    mock_llm_response = json.dumps({
        'summary': 'Multiple system issues detected including database and storage problems.',
        'categories': ['Database', 'Storage', 'Memory'],
        'severity_breakdown': {'ERROR': len([a for a in alerts if a['level'] == 'ERROR']),
                              'WARNING': len([a for a in alerts if a['level'] == 'WARNING'])},
        'root_causes': ['Database connectivity', 'Disk I/O issues', 'Resource constraints']
    })
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        llm_agent = LLMAlertSummaryAgent("LLMAlertSummary")
        result = llm_agent.run(alerts)
    
    # Step 3: Verify integration
    print("\nStep 3: Validating integration...")
    
    assert result['alerts'] == alerts, "Alerts should be passed through unchanged"
    print("  ✓ Alerts passed through correctly")
    
    assert 'llm_summary' in result, "Result should contain LLM summary"
    print("  ✓ LLM summary generated")
    
    llm_summary = result['llm_summary']
    print(f"\n  Summary: {llm_summary['summary']}")
    print(f"  Categories: {', '.join(llm_summary['categories'])}")
    print(f"  Severity: {llm_summary['severity_breakdown']}")
    print(f"  Root Causes: {len(llm_summary['root_causes'])} identified")
    
    # Verify the summary reflects actual alert counts
    error_count = len([a for a in alerts if a['level'] == 'ERROR'])
    warning_count = len([a for a in alerts if a['level'] == 'WARNING'])
    
    assert llm_summary['severity_breakdown']['ERROR'] == error_count
    assert llm_summary['severity_breakdown']['WARNING'] == warning_count
    print(f"\n  ✓ Severity counts match: {error_count} ERRORs, {warning_count} WARNINGs")
    
    print("\n" + "="*60)
    print("✓ Integration test passed successfully")
    print("="*60)
    
    return result


if __name__ == "__main__":
    test_monitor_to_llm_summary_integration()
    
    print("\n" + "="*60)
    print("MONITOR -> LLM SUMMARY INTEGRATION TEST PASSED ✓")
    print("="*60)
