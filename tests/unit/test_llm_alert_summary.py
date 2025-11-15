#!/usr/bin/env python3
"""Test to verify LLMAlertSummaryAgent implementation."""

import json
from unittest.mock import Mock, patch
from agents.llm_alert_summary_agent import LLMAlertSummaryAgent


def test_llm_alert_summary_agent():
    """Test the LLMAlertSummaryAgent with mock LLM response."""
    
    print("\n" + "="*60)
    print("LLM ALERT SUMMARY AGENT TEST")
    print("="*60)
    
    # Sample alerts from MonitorAgent
    sample_alerts = [
        {
            'timestamp': '2025-11-10 10:01:03',
            'level': 'ERROR',
            'message': 'Database connection timeout',
            'line_number': 1,
            'raw_log': '2025-11-10 10:01:03 ERROR Database connection timeout'
        },
        {
            'timestamp': '2025-11-10 10:02:47',
            'level': 'WARNING',
            'message': 'Memory threshold exceeded',
            'line_number': 2,
            'raw_log': '2025-11-10 10:02:47 WARNING Memory threshold exceeded'
        },
        {
            'timestamp': '2025-11-10 10:07:33',
            'level': 'ERROR',
            'message': 'Failed to write to disk: /var/log/app.log',
            'line_number': 4,
            'raw_log': '2025-11-10 10:07:33 ERROR Failed to write to disk: /var/log/app.log'
        }
    ]
    
    # Mock LLM response
    mock_llm_response = json.dumps({
        'summary': 'System experiencing database connectivity issues and disk write failures, with memory pressure warnings.',
        'categories': ['Database', 'Storage', 'Memory'],
        'severity_breakdown': {'ERROR': 2, 'WARNING': 1},
        'root_causes': [
            'Database connection pool exhaustion',
            'Disk space or permission issues',
            'Memory leak or high load'
        ]
    })
    
    # Create agent with mocked LLM client
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        agent = LLMAlertSummaryAgent("LLMAlertSummary")
        result = agent.run(sample_alerts)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'alerts' in result, "Result must contain 'alerts' field"
    assert 'llm_summary' in result, "Result must contain 'llm_summary' field"
    print("  ✓ Result has required fields: 'alerts', 'llm_summary'")
    
    # Verify alerts are passed through
    assert result['alerts'] == sample_alerts, "Original alerts should be passed through"
    print(f"  ✓ Original {len(sample_alerts)} alerts passed through")
    
    # Verify LLM summary structure
    llm_summary = result['llm_summary']
    assert 'summary' in llm_summary, "LLM summary must have 'summary' field"
    assert 'categories' in llm_summary, "LLM summary must have 'categories' field"
    assert 'severity_breakdown' in llm_summary, "LLM summary must have 'severity_breakdown' field"
    assert 'root_causes' in llm_summary, "LLM summary must have 'root_causes' field"
    print("  ✓ LLM summary has all required fields")
    
    # Verify summary content
    assert isinstance(llm_summary['summary'], str), "Summary should be a string"
    assert len(llm_summary['summary']) > 0, "Summary should not be empty"
    print(f"  ✓ Summary: {llm_summary['summary'][:80]}...")
    
    assert isinstance(llm_summary['categories'], list), "Categories should be a list"
    print(f"  ✓ Categories: {', '.join(llm_summary['categories'])}")
    
    assert isinstance(llm_summary['severity_breakdown'], dict), "Severity breakdown should be a dict"
    print(f"  ✓ Severity breakdown: {llm_summary['severity_breakdown']}")
    
    assert isinstance(llm_summary['root_causes'], list), "Root causes should be a list"
    print(f"  ✓ Root causes: {len(llm_summary['root_causes'])} identified")
    
    print("\n" + "="*60)
    print("✓ LLMAlertSummaryAgent test passed successfully")
    print("="*60)
    
    return result


def test_llm_alert_summary_empty_alerts():
    """Test LLMAlertSummaryAgent with empty alert list."""
    
    print("\n" + "="*60)
    print("LLM ALERT SUMMARY TEST - EMPTY ALERTS")
    print("="*60)
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        agent = LLMAlertSummaryAgent("LLMAlertSummary")
        result = agent.run([])
    
    # Should handle empty list gracefully
    assert result['alerts'] == [], "Should return empty alerts list"
    assert 'llm_summary' in result, "Should still provide summary"
    assert result['llm_summary']['summary'] == 'No alerts detected.', "Should indicate no alerts"
    
    print("  ✓ Handles empty alert list gracefully")
    print("  ✓ Returns appropriate 'no alerts' summary")
    
    print("\n" + "="*60)
    print("✓ Empty alerts test passed")
    print("="*60)
    
    return result


def test_llm_alert_summary_fallback():
    """Test LLMAlertSummaryAgent fallback when LLM fails."""
    
    print("\n" + "="*60)
    print("LLM ALERT SUMMARY TEST - FALLBACK")
    print("="*60)
    
    sample_alerts = [
        {
            'timestamp': '2025-11-10 10:01:03',
            'level': 'ERROR',
            'message': 'Test error',
            'line_number': 1,
            'raw_log': '2025-11-10 10:01:03 ERROR Test error'
        }
    ]
    
    # Mock LLM to raise an exception
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.side_effect = Exception("LLM API error")
        MockClient.return_value = mock_client_instance
        
        agent = LLMAlertSummaryAgent("LLMAlertSummary")
        result = agent.run(sample_alerts)
    
    # Should fall back to basic summary
    assert 'alerts' in result, "Should still return alerts"
    assert 'llm_summary' in result, "Should provide fallback summary"
    
    llm_summary = result['llm_summary']
    assert 'summary' in llm_summary, "Fallback should have summary"
    assert 'ERROR' in llm_summary['severity_breakdown'], "Fallback should count severity levels"
    
    print("  ✓ Handles LLM failure gracefully")
    print("  ✓ Provides fallback summary")
    print(f"  ✓ Fallback summary: {llm_summary['summary']}")
    
    print("\n" + "="*60)
    print("✓ Fallback test passed")
    print("="*60)
    
    return result


if __name__ == "__main__":
    # Run all tests
    test_llm_alert_summary_agent()
    test_llm_alert_summary_empty_alerts()
    test_llm_alert_summary_fallback()
    
    print("\n" + "="*60)
    print("ALL LLM ALERT SUMMARY AGENT TESTS PASSED ✓")
    print("="*60)
