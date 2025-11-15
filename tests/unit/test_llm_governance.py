#!/usr/bin/env python3
"""Test to verify LLMGovernanceAgent implementation."""

import json
from unittest.mock import Mock, patch
from agents.llm_governance_agent import LLMGovernanceAgent


def test_llm_governance_agent():
    """Test the LLMGovernanceAgent with mock LLM response."""
    
    print("\n" + "="*60)
    print("LLM GOVERNANCE AGENT TEST")
    print("="*60)
    
    # Sample audit summary from OpsLogAgent
    sample_audit_summary = {
        'status': 'logged',
        'count': 4,
        'timestamp': '2025-11-16 04:33:21',
        'output_path': 'data/output_log.json'
    }
    
    # Mock LLM response
    mock_llm_response = json.dumps({
        'risk': 'high',
        'escalation': 'Immediate review and action required by the incident response team due to multiple high-severity incidents.',
        'compliance_issues': [
            'Multiple high-severity incidents detected without automated remediation',
            'Incident response time may exceed SLA thresholds'
        ],
        'commentary': 'The log summary indicates 4 incidents with significant high-severity alerts. The distribution across multiple categories suggests potential systemic issues requiring immediate attention.'
    })
    
    # Create agent with mocked LLM client and mocked file loading
    with patch('agents.llm_governance_agent.OpenAIClient') as MockClient, \
         patch('agents.llm_governance_agent.LLMGovernanceAgent._load_audit_log') as MockLoadLog:
        
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        # Mock audit log data
        MockLoadLog.return_value = {
            'execution_timestamp': '2025-11-16 04:33:21',
            'total_incidents': 4,
            'stage_outputs': {
                'triage_stage': {
                    'severity_distribution': {'high': 2, 'medium': 2}
                }
            },
            'recommendations_summary': {
                'high_priority_count': 2
            }
        }
        
        agent = LLMGovernanceAgent("LLMGovernance")
        result = agent.run(sample_audit_summary)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'audit_summary' in result, "Result must contain 'audit_summary' field"
    assert 'governance_analysis' in result, "Result must contain 'governance_analysis' field"
    print("  ✓ Result has required fields: 'audit_summary', 'governance_analysis'")
    
    # Verify audit summary is passed through
    assert result['audit_summary'] == sample_audit_summary, "Original audit summary should be passed through"
    print(f"  ✓ Original audit summary passed through")
    
    # Verify governance analysis structure
    governance = result['governance_analysis']
    assert 'risk' in governance, "Governance analysis must have 'risk' field"
    assert 'escalation' in governance, "Governance analysis must have 'escalation' field"
    assert 'compliance_issues' in governance, "Governance analysis must have 'compliance_issues' field"
    assert 'commentary' in governance, "Governance analysis must have 'commentary' field"
    print("  ✓ Governance analysis has all required fields")
    
    # Verify risk level
    assert governance['risk'] in ['low', 'medium', 'high', 'critical'], "Risk must be valid level"
    print(f"  ✓ Risk Level: {governance['risk']}")
    
    # Verify escalation
    assert isinstance(governance['escalation'], str), "Escalation should be a string"
    assert len(governance['escalation']) > 0, "Escalation should not be empty"
    print(f"  ✓ Escalation: {governance['escalation'][:60]}...")
    
    # Verify compliance issues
    assert isinstance(governance['compliance_issues'], list), "Compliance issues should be a list"
    print(f"  ✓ Compliance Issues: {len(governance['compliance_issues'])} identified")
    
    # Verify commentary
    assert isinstance(governance['commentary'], str), "Commentary should be a string"
    assert len(governance['commentary']) > 0, "Commentary should not be empty"
    print(f"  ✓ Commentary: {governance['commentary'][:80]}...")
    
    print("\n" + "="*60)
    print("✓ LLMGovernanceAgent test passed successfully")
    print("="*60)
    
    return result


def test_llm_governance_no_data():
    """Test LLMGovernanceAgent with no audit data."""
    
    print("\n" + "="*60)
    print("LLM GOVERNANCE TEST - NO DATA")
    print("="*60)
    
    sample_audit_summary = {
        'status': 'no_data',
        'count': 0,
        'timestamp': None,
        'output_path': None
    }
    
    with patch('agents.llm_governance_agent.OpenAIClient') as MockClient:
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        agent = LLMGovernanceAgent("LLMGovernance")
        result = agent.run(sample_audit_summary)
    
    # Should handle no data gracefully
    assert result['audit_summary'] == sample_audit_summary, "Should return audit summary"
    assert 'governance_analysis' in result, "Should still provide analysis"
    
    governance = result['governance_analysis']
    assert governance['risk'] == 'low', "No data should result in low risk"
    assert governance['escalation'] == 'None required', "No escalation needed for no data"
    assert governance['compliance_issues'] == [], "No compliance issues for no data"
    
    print("  ✓ Handles no data gracefully")
    print("  ✓ Returns low risk assessment")
    print(f"  ✓ Commentary: {governance['commentary']}")
    
    print("\n" + "="*60)
    print("✓ No data test passed")
    print("="*60)
    
    return result


def test_llm_governance_fallback():
    """Test LLMGovernanceAgent fallback when LLM fails."""
    
    print("\n" + "="*60)
    print("LLM GOVERNANCE TEST - FALLBACK")
    print("="*60)
    
    sample_audit_summary = {
        'status': 'logged',
        'count': 12,
        'timestamp': '2025-11-16 04:33:21',
        'output_path': 'data/output_log.json'
    }
    
    # Mock LLM to raise an exception
    with patch('agents.llm_governance_agent.OpenAIClient') as MockClient, \
         patch('agents.llm_governance_agent.LLMGovernanceAgent._load_audit_log') as MockLoadLog:
        
        mock_client_instance = Mock()
        mock_client_instance.generate.side_effect = Exception("LLM API error")
        MockClient.return_value = mock_client_instance
        
        MockLoadLog.return_value = {}
        
        agent = LLMGovernanceAgent("LLMGovernance")
        result = agent.run(sample_audit_summary)
    
    # Should fall back to basic analysis
    assert 'audit_summary' in result, "Should still return audit summary"
    assert 'governance_analysis' in result, "Should provide fallback analysis"
    
    governance = result['governance_analysis']
    assert 'risk' in governance, "Fallback should have risk"
    assert 'escalation' in governance, "Fallback should have escalation"
    assert 'compliance_issues' in governance, "Fallback should have compliance issues"
    
    # With 12 incidents, should be critical risk
    assert governance['risk'] == 'critical', "12 incidents should trigger critical risk"
    assert 'Immediate escalation' in governance['escalation'], "Should recommend immediate escalation"
    
    print("  ✓ Handles LLM failure gracefully")
    print("  ✓ Provides fallback analysis based on incident count")
    print(f"  ✓ Fallback risk: {governance['risk']}")
    print(f"  ✓ Fallback escalation: {governance['escalation']}")
    
    print("\n" + "="*60)
    print("✓ Fallback test passed")
    print("="*60)
    
    return result


def test_llm_governance_risk_levels():
    """Test LLMGovernanceAgent fallback risk level calculation."""
    
    print("\n" + "="*60)
    print("LLM GOVERNANCE TEST - RISK LEVELS")
    print("="*60)
    
    test_cases = [
        (0, 'low'),
        (2, 'low'),
        (5, 'medium'),
        (8, 'high'),
        (15, 'critical')
    ]
    
    for count, expected_risk in test_cases:
        sample_audit_summary = {
            'status': 'logged',
            'count': count,
            'timestamp': '2025-11-16 04:33:21',
            'output_path': 'data/output_log.json'
        }
        
        with patch('agents.llm_governance_agent.OpenAIClient') as MockClient, \
             patch('agents.llm_governance_agent.LLMGovernanceAgent._load_audit_log') as MockLoadLog:
            
            mock_client_instance = Mock()
            mock_client_instance.generate.side_effect = Exception("Force fallback")
            MockClient.return_value = mock_client_instance
            MockLoadLog.return_value = {}
            
            agent = LLMGovernanceAgent("LLMGovernance")
            result = agent.run(sample_audit_summary)
        
        governance = result['governance_analysis']
        assert governance['risk'] == expected_risk, f"Expected {expected_risk} for {count} incidents"
        print(f"  ✓ {count} incidents → {expected_risk} risk")
    
    print("\n" + "="*60)
    print("✓ Risk level calculation test passed")
    print("="*60)


if __name__ == "__main__":
    # Run all tests
    test_llm_governance_agent()
    test_llm_governance_no_data()
    test_llm_governance_fallback()
    test_llm_governance_risk_levels()
    
    print("\n" + "="*60)
    print("ALL LLM GOVERNANCE AGENT TESTS PASSED ✓")
    print("="*60)
