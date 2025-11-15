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
    
    # Sample resolution plans from ResolutionAgent
    sample_plans = [
        {
            'alert_id': '2025-11-10 10:01:03_1',
            'timestamp': '2025-11-10 10:01:03',
            'severity': 'critical',
            'category': 'database',
            'message': 'Database connection timeout',
            'recommended_actions': [
                'Initiate database failover to standby instance',
                'Alert DBA team immediately',
                'Check database connection pool status'
            ],
            'priority': 1,
            'reasoning': 'Based on critical severity database incident, recommended actions prioritize immediate stabilization and root cause analysis.'
        },
        {
            'alert_id': '2025-11-10 10:02:47_2',
            'timestamp': '2025-11-10 10:02:47',
            'severity': 'high',
            'category': 'memory',
            'message': 'Memory threshold exceeded',
            'recommended_actions': [
                'Analyze heap dump',
                'Review memory usage trends',
                'Consider scaling up resources'
            ],
            'priority': 2,
            'reasoning': 'Based on high severity memory incident, recommended actions prioritize immediate stabilization and root cause analysis.'
        }
    ]
    
    # Mock LLM response
    mock_llm_response = json.dumps({
        'summary': 'Critical database failover required with concurrent memory pressure. Immediate action needed on database systems, followed by memory analysis.',
        'recommendations': [
            'Execute database failover immediately',
            'Alert DBA and infrastructure teams',
            'Monitor memory usage during failover',
            'Prepare for potential resource scaling'
        ],
        'escalation': 'Immediate escalation to on-call DBA and infrastructure lead required',
        'affected_systems': ['Database', 'Application Server', 'Memory Management']
    })
    
    # Create agent with mocked LLM client
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        agent = LLMResolutionAgent("LLMResolution")
        result = agent.run(sample_plans)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'resolution_plans' in result, "Result must contain 'resolution_plans' field"
    assert 'llm_resolution_summary' in result, "Result must contain 'llm_resolution_summary' field"
    print("  ✓ Result has required fields: 'resolution_plans', 'llm_resolution_summary'")
    
    # Verify resolution plans are passed through
    assert result['resolution_plans'] == sample_plans, "Original resolution plans should be passed through"
    print(f"  ✓ Original {len(sample_plans)} resolution plans passed through")
    
    # Verify LLM summary structure
    llm_summary = result['llm_resolution_summary']
    assert 'summary' in llm_summary, "LLM summary must have 'summary' field"
    assert 'recommendations' in llm_summary, "LLM summary must have 'recommendations' field"
    assert 'escalation' in llm_summary, "LLM summary must have 'escalation' field"
    assert 'affected_systems' in llm_summary, "LLM summary must have 'affected_systems' field"
    print("  ✓ LLM summary has all required fields")
    
    # Verify summary content
    assert isinstance(llm_summary['summary'], str), "Summary should be a string"
    assert len(llm_summary['summary']) > 0, "Summary should not be empty"
    print(f"  ✓ Summary: {llm_summary['summary'][:80]}...")
    
    assert isinstance(llm_summary['recommendations'], list), "Recommendations should be a list"
    print(f"  ✓ Recommendations: {len(llm_summary['recommendations'])} items")
    
    assert isinstance(llm_summary['escalation'], str), "Escalation should be a string"
    print(f"  ✓ Escalation: {llm_summary['escalation'][:60]}...")
    
    assert isinstance(llm_summary['affected_systems'], list), "Affected systems should be a list"
    print(f"  ✓ Affected systems: {', '.join(llm_summary['affected_systems'])}")
    
    print("\n" + "="*60)
    print("✓ LLMResolutionAgent test passed successfully")
    print("="*60)
    
    return result


def test_llm_resolution_empty_plans():
    """Test LLMResolutionAgent with empty resolution plans list."""
    
    print("\n" + "="*60)
    print("LLM RESOLUTION TEST - EMPTY PLANS")
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
    
    print("  ✓ Handles empty resolution plans list gracefully")
    print("  ✓ Returns appropriate 'no plans' summary")
    
    print("\n" + "="*60)
    print("✓ Empty plans test passed")
    print("="*60)
    
    return result


def test_llm_resolution_fallback():
    """Test LLMResolutionAgent fallback when LLM fails."""
    
    print("\n" + "="*60)
    print("LLM RESOLUTION TEST - FALLBACK")
    print("="*60)
    
    sample_plans = [
        {
            'alert_id': '2025-11-10 10:01:03_1',
            'timestamp': '2025-11-10 10:01:03',
            'severity': 'critical',
            'category': 'database',
            'message': 'Test error',
            'recommended_actions': ['Action 1', 'Action 2'],
            'priority': 1,
            'reasoning': 'Test reasoning'
        }
    ]
    
    # Mock LLM to raise an exception
    with patch('agents.llm_resolution_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        mock_client_instance.generate.side_effect = Exception("LLM API error")
        MockClient.return_value = mock_client_instance
        
        agent = LLMResolutionAgent("LLMResolution")
        result = agent.run(sample_plans)
    
    # Should fall back to basic summary
    assert 'resolution_plans' in result, "Should still return resolution plans"
    assert 'llm_resolution_summary' in result, "Should provide fallback summary"
    
    llm_summary = result['llm_resolution_summary']
    assert 'summary' in llm_summary, "Fallback should have summary"
    assert 'escalation' in llm_summary, "Fallback should have escalation"
    assert 'Immediate escalation' in llm_summary['escalation'], "Critical severity should trigger escalation"
    
    print("  ✓ Handles LLM failure gracefully")
    print("  ✓ Provides fallback summary")
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
