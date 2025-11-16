#!/usr/bin/env python3
"""Test to verify LLMResolutionAgent implementation."""

import json
from unittest.mock import Mock, patch
from agents.llm_resolution_agent import LLMResolutionAgent


def test_llm_resolution_agent():
    """Test the LLMResolutionAgent with mock LLM response."""
    
    print("\n" + "="*60)
    print("LLM RESOLUTION AGENT TEST")
    print("="*60)
    
    # Sample triaged alerts from TriageAgent
    sample_alerts = [
        {
            'timestamp': '2025-11-10 10:01:03',
            'level': 'ERROR',
            'severity': 'critical',
            'category': 'database',
            'message': 'Database connection timeout',
            'line_number': 1
        },
        {
            'timestamp': '2025-11-10 10:02:47',
            'level': 'ERROR',
            'severity': 'high',
            'category': 'memory',
            'message': 'Memory threshold exceeded',
            'line_number': 2
        }
    ]
    
    # Mock LLM response with resolution plans
    mock_llm_response = json.dumps({
        'resolution_plans': [
            {
                'alert_id': '2025-11-10 10:01:03_0',
                'severity': 'critical',
                'category': 'database',
                'message': 'Database connection timeout',
                'recommended_actions': [
                    'Initiate database failover to standby instance',
                    'Alert DBA team immediately',
                    'Check database connection pool status'
                ],
                'priority': 1,
                'reasoning': 'Critical database issue requires immediate failover'
            },
            {
                'alert_id': '2025-11-10 10:02:47_1',
                'severity': 'high',
                'category': 'memory',
                'message': 'Memory threshold exceeded',
                'recommended_actions': [
                    'Analyze heap dump',
                    'Review memory usage trends',
                    'Consider scaling up resources'
                ],
                'priority': 2,
                'reasoning': 'High memory usage requires investigation'
            }
        ],
        'summary': 'Critical database failover required with concurrent memory pressure. Immediate action needed on database systems, followed by memory analysis.',
        'escalation': 'Immediate escalation to on-call DBA and infrastructure lead required',
        'affected_systems': ['Database', 'Application Server', 'Memory Management']
    })
    
    # Create agent with mocked LLM client
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        agent = LLMResolutionAgent("LLMResolution")
        result = agent.run(sample_alerts)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'resolution_plans' in result, "Result must contain 'resolution_plans' field"
    assert 'llm_resolution_summary' in result, "Result must contain 'llm_resolution_summary' field"
    print("  ✓ Result has required fields: 'resolution_plans', 'llm_resolution_summary'")
    
    # Verify resolution plans were generated
    assert len(result['resolution_plans']) == len(sample_alerts), "Should generate one plan per alert"
    print(f"  ✓ Generated {len(result['resolution_plans'])} resolution plans")
    
    # Verify each resolution plan has required fields
    for plan in result['resolution_plans']:
        assert 'alert_id' in plan, "Plan must have alert_id"
        assert 'severity' in plan, "Plan must have severity"
        assert 'category' in plan, "Plan must have category"
        assert 'recommended_actions' in plan, "Plan must have recommended_actions"
        assert 'priority' in plan, "Plan must have priority"
        assert 'reasoning' in plan, "Plan must have reasoning"
    print("  ✓ All resolution plans have required fields")
    
    # Verify LLM summary structure
    llm_summary = result['llm_resolution_summary']
    assert 'summary' in llm_summary, "LLM summary must have 'summary' field"
    assert 'escalation' in llm_summary, "LLM summary must have 'escalation' field"
    assert 'affected_systems' in llm_summary, "LLM summary must have 'affected_systems' field"
    print("  ✓ LLM summary has all required fields")
    
    # Verify summary content
    assert isinstance(llm_summary['summary'], str), "Summary should be a string"
    assert len(llm_summary['summary']) > 0, "Summary should not be empty"
    print(f"  ✓ Summary: {llm_summary['summary'][:80]}...")
    
    assert isinstance(llm_summary['escalation'], str), "Escalation should be a string"
    print(f"  ✓ Escalation: {llm_summary['escalation'][:60]}...")
    
    assert isinstance(llm_summary['affected_systems'], list), "Affected systems should be a list"
    print(f"  ✓ Affected systems: {', '.join(llm_summary['affected_systems'])}")
    
    print("\n" + "="*60)
    print("✓ LLMResolutionAgent test passed successfully")
    print("="*60)
    
    return result


def test_llm_resolution_empty_plans():
    """Test LLMResolutionAgent with empty alerts list."""
    
    print("\n" + "="*60)
    print("LLM RESOLUTION TEST - EMPTY ALERTS")
    print("="*60)
    
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        agent = LLMResolutionAgent("LLMResolution")
        result = agent.run([])
    
    # Should handle empty list gracefully
    assert result['resolution_plans'] == [], "Should return empty resolution plans list"
    assert 'llm_resolution_summary' in result, "Should still provide summary"
    assert result['llm_resolution_summary']['summary'] == 'No resolution plans generated.', "Should indicate no plans"
    
    print("  ✓ Handles empty alerts list gracefully")
    print("  ✓ Returns appropriate 'no plans' summary")
    
    print("\n" + "="*60)
    print("✓ Empty alerts test passed")
    print("="*60)
    
    return result


def test_llm_resolution_fallback():
    """Test LLMResolutionAgent fallback when LLM fails."""
    
    print("\n" + "="*60)
    print("LLM RESOLUTION TEST - FALLBACK")
    print("="*60)
    
    sample_alerts = [
        {
            'timestamp': '2025-11-10 10:01:03',
            'level': 'ERROR',
            'severity': 'critical',
            'category': 'database',
            'message': 'Test error',
            'line_number': 1
        }
    ]
    
    # Mock LLM to raise an exception
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.side_effect = Exception("LLM API error")
        MockClient.return_value = mock_client_instance
        
        agent = LLMResolutionAgent("LLMResolution")
        result = agent.run(sample_alerts)
    
    # Should fall back to basic resolution plans
    assert 'resolution_plans' in result, "Should still return resolution plans"
    assert 'llm_resolution_summary' in result, "Should provide fallback summary"
    assert len(result['resolution_plans']) == len(sample_alerts), "Should generate fallback plans"
    
    # Verify fallback plan structure
    plan = result['resolution_plans'][0]
    assert 'alert_id' in plan, "Fallback plan should have alert_id"
    assert 'recommended_actions' in plan, "Fallback plan should have recommended_actions"
    assert len(plan['recommended_actions']) > 0, "Fallback should provide actions"
    
    llm_summary = result['llm_resolution_summary']
    assert 'summary' in llm_summary, "Fallback should have summary"
    assert 'escalation' in llm_summary, "Fallback should have escalation"
    assert 'Immediate escalation' in llm_summary['escalation'], "Critical severity should trigger escalation"
    
    print("  ✓ Handles LLM failure gracefully")
    print("  ✓ Provides fallback resolution plans")
    print(f"  ✓ Fallback summary: {llm_summary['summary']}")
    print(f"  ✓ Fallback escalation: {llm_summary['escalation']}")
    
    print("\n" + "="*60)
    print("✓ Fallback test passed")
    print("="*60)
    
    return result


if __name__ == "__main__":
    # Run all tests
    test_llm_resolution_agent()
    test_llm_resolution_empty_plans()
    test_llm_resolution_fallback()
    
    print("\n" + "="*60)
    print("ALL LLM RESOLUTION AGENT TESTS PASSED ✓")
    print("="*60)
