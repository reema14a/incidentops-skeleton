#!/usr/bin/env python3
"""Test to verify GovernanceInsightsAgent implementation."""

import json
from unittest.mock import Mock, patch
from agents.llm_governance_insights_agent import GovernanceInsightsAgent


def test_llm_governance_insights_agent():
    """Test the GovernanceInsightsAgent with mock LLM response and DB data."""
    
    print("\n" + "="*60)
    print("GOVERNANCE INSIGHTS AGENT TEST")
    print("="*60)
    
    # Sample governance output from LLMGovernanceAgent
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 4,
            'timestamp': '2025-11-16 04:33:21'
        },
        'governance_analysis': {
            'risk': 'high',
            'escalation': 'Immediate review required',
            'escalation_category': 'incident_team',
            'compliance_issues': ['Issue 1', 'Issue 2'],
            'commentary': 'Multiple high-severity incidents detected'
        }
    }
    
    # Mock LLM response
    mock_llm_response = json.dumps({
        'trend_summary': ['System shows increasing incident frequency over the past 10 runs with a shift toward higher severity classifications.'],
        'risk_trend': ['Risk levels have escalated from predominantly low/medium to high/critical in recent runs, indicating deteriorating system stability.'],
        'compliance_trend': ['Compliance issues have increased by 40% compared to historical average, with recurring themes around security patches and access control.'],
        'recurring_issues': [
            'Unauthorized access attempts',
            'Missing security patches',
            'Configuration drift in production'
        ],
        'category_hotspots': [
            'security',
            'network',
            'performance'
        ],
        'recommendations': [
            'Implement automated security patch management',
            'Review and tighten access control policies',
            'Establish configuration management baseline',
            'Increase monitoring frequency for security category'
        ],
        'anomaly_detection': ['Detected unusual spike in network-related incidents on 2025-11-15, suggesting potential infrastructure issue or attack pattern.']
    })
    
    # Mock DB utility functions
    mock_risk_trend = [
        {'run_id': 1, 'timestamp': '2025-11-15T10:00:00.000000', 'risk': 'low', 'date': '2025-11-15', 'time': '10:00:00'},
        {'run_id': 2, 'timestamp': '2025-11-15T11:00:00.000000', 'risk': 'medium', 'date': '2025-11-15', 'time': '11:00:00'},
        {'run_id': 3, 'timestamp': '2025-11-15T12:00:00.000000', 'risk': 'high', 'date': '2025-11-15', 'time': '12:00:00'}
    ]
    
    mock_compliance_trend = [
        {'run_id': 1, 'timestamp': '2025-11-15T10:00:00.000000', 'issue_count': 0, 'date': '2025-11-15', 'time': '10:00:00'},
        {'run_id': 2, 'timestamp': '2025-11-15T11:00:00.000000', 'issue_count': 2, 'date': '2025-11-15', 'time': '11:00:00'},
        {'run_id': 3, 'timestamp': '2025-11-15T12:00:00.000000', 'issue_count': 3, 'date': '2025-11-15', 'time': '12:00:00'}
    ]
    
    mock_escalation_counts = {
        'None required': 5,
        'Monitor for recurring patterns': 3,
        'Escalate to on-call engineer': 2
    }
    
    mock_recent_runs = [
        {
            'run_id': 1,
            'timestamp': '2025-11-15T10:00:00.000000',
            'alerts_count': 2,
            'raw_data_path': 'data/samples/sample_logs.txt',
            'audit_data': json.dumps({'total_incidents': 2}),
            'governance_data': json.dumps({'risk': 'low', 'escalation_category': 'none'})
        },
        {
            'run_id': 2,
            'timestamp': '2025-11-15T11:00:00.000000',
            'alerts_count': 5,
            'raw_data_path': 'data/samples/sample_logs.txt',
            'audit_data': json.dumps({'total_incidents': 5}),
            'governance_data': json.dumps({'risk': 'medium', 'escalation_category': 'monitor'})
        }
    ]
    
    mock_category_distribution = {
        'security': 10,
        'network': 8,
        'performance': 5
    }
    
    mock_severity_distribution = {
        'critical': 3,
        'high': 7,
        'medium': 10,
        'low': 5
    }
    
    # Create agent with mocked LLM client and DB functions
    with patch('agents.llm_governance_insights_agent.OpenAIClient') as MockClient, \
         patch('agents.llm_governance_insights_agent.db_util') as mock_db_util:
        
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_llm_response
        MockClient.return_value = mock_client_instance
        
        # Mock DB utility functions
        mock_db_util.get_risk_trend.return_value = mock_risk_trend
        mock_db_util.get_compliance_trend.return_value = mock_compliance_trend
        mock_db_util.get_escalation_text_counts.return_value = mock_escalation_counts
        mock_db_util.get_recent_runs.return_value = mock_recent_runs
        mock_db_util.get_category_distribution.return_value = mock_category_distribution
        mock_db_util.get_severity_distribution.return_value = mock_severity_distribution
        
        agent = GovernanceInsightsAgent("GovernanceInsights")
        result = agent.run(sample_governance_output)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'governance_output' in result, "Result must contain 'governance_output' field"
    assert 'insights' in result, "Result must contain 'insights' field"
    print("  ✓ Result has required fields: 'governance_output', 'insights'")
    
    # Verify governance output is passed through
    assert result['governance_output'] == sample_governance_output, "Original governance output should be passed through"
    print(f"  ✓ Original governance output passed through")
    
    # Verify insights structure
    insights = result['insights']
    required_fields = [
        'trend_summary',
        'risk_trend',
        'compliance_trend',
        'recurring_issues',
        'category_hotspots',
        'recommendations',
        'anomaly_detection'
    ]
    
    for field in required_fields:
        assert field in insights, f"Insights must have '{field}' field"
    print("  ✓ Insights has all required fields")
    
    # Verify trend summary
    assert isinstance(insights['trend_summary'], list), "Trend summary should be a list"
    assert len(insights['trend_summary']) > 0, "Trend summary should not be empty"
    print(f"  ✓ Trend Summary: {insights['trend_summary'][:80]}...")
    
    # Verify risk trend
    assert isinstance(insights['risk_trend'], list), "Risk trend should be a list"
    print(f"  ✓ Risk Trend: {insights['risk_trend'][:80]}...")
    
    # Verify compliance trend
    assert isinstance(insights['compliance_trend'], list), "Compliance trend should be a list"
    print(f"  ✓ Compliance Trend: {insights['compliance_trend'][:80]}...")
    
    # Verify recurring issues
    assert isinstance(insights['recurring_issues'], list), "Recurring issues should be a list"
    print(f"  ✓ Recurring Issues: {len(insights['recurring_issues'])} identified")
    
    # Verify category hotspots
    assert isinstance(insights['category_hotspots'], list), "Category hotspots should be a list"
    print(f"  ✓ Category Hotspots: {len(insights['category_hotspots'])} identified")
    
    # Verify recommendations
    assert isinstance(insights['recommendations'], list), "Recommendations should be a list"
    assert len(insights['recommendations']) > 0, "Should have at least one recommendation"
    print(f"  ✓ Recommendations: {len(insights['recommendations'])} provided")
    
    # Verify anomaly detection
    assert isinstance(insights['anomaly_detection'], list), "Anomaly detection should be a list"
    print(f"  ✓ Anomaly Detection: {insights['anomaly_detection'][:80]}...")
    
    # Verify DB functions were called
    mock_db_util.get_risk_trend.assert_called_once()
    mock_db_util.get_compliance_trend.assert_called_once()
    mock_db_util.get_escalation_text_counts.assert_called_once()
    mock_db_util.get_recent_runs.assert_called_once_with(limit=10)
    mock_db_util.get_category_distribution.assert_called_once()
    mock_db_util.get_severity_distribution.assert_called_once()
    print("  ✓ All DB utility functions called correctly")
    
    print("\n" + "="*60)
    print("✓ GovernanceInsightsAgent test passed successfully")
    print("="*60)
    
    return result


def test_governance_insights_no_data():
    """Test GovernanceInsightsAgent with no historical data."""
    
    print("\n" + "="*60)
    print("GOVERNANCE INSIGHTS TEST - NO DATA")
    print("="*60)
    
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 1,
            'timestamp': '2025-11-16 04:33:21'
        },
        'governance_analysis': {
            'risk': 'low',
            'escalation': 'None required',
            'escalation_category': 'none',
            'compliance_issues': [],
            'commentary': 'First run'
        }
    }
    
    # Mock DB utility functions to return empty data
    with patch('agents.llm_governance_insights_agent.OpenAIClient') as MockClient, \
         patch('agents.llm_governance_insights_agent.db_util') as mock_db_util:
        
        mock_client_instance = Mock()
        MockClient.return_value = mock_client_instance
        
        # Mock DB utility functions to return empty data
        mock_db_util.get_risk_trend.return_value = []
        mock_db_util.get_compliance_trend.return_value = []
        mock_db_util.get_escalation_text_counts.return_value = {}
        mock_db_util.get_recent_runs.return_value = []
        mock_db_util.get_category_distribution.return_value = {}
        mock_db_util.get_severity_distribution.return_value = {}
        
        agent = GovernanceInsightsAgent("GovernanceInsights")
        result = agent.run(sample_governance_output)
    
    # Should handle no data gracefully
    assert result['governance_output'] == sample_governance_output, "Should return governance output"
    assert 'insights' in result, "Should still provide insights"
    
    insights = result['insights']
    assert 'Insufficient historical data' in insights['trend_summary'], "Should indicate insufficient data"
    assert isinstance(insights['recommendations'], list), "Should provide recommendations"
    assert len(insights['recommendations']) > 0, "Should have at least one recommendation"
    
    print("  ✓ Handles no data gracefully")
    print("  ✓ Provides helpful message about insufficient data")
    print(f"  ✓ Trend Summary: {insights['trend_summary']}")
    print(f"  ✓ Recommendations: {len(insights['recommendations'])}")
    
    print("\n" + "="*60)
    print("✓ No data test passed")
    print("="*60)
    
    return result


def test_governance_insights_fallback():
    """Test GovernanceInsightsAgent fallback when LLM fails."""
    
    print("\n" + "="*60)
    print("GOVERNANCE INSIGHTS TEST - FALLBACK")
    print("="*60)
    
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 5,
            'timestamp': '2025-11-16 04:33:21'
        },
        'governance_analysis': {
            'risk': 'medium',
            'escalation': 'Monitor',
            'escalation_category': 'monitor',
            'compliance_issues': ['Issue 1'],
            'commentary': 'Some incidents detected'
        }
    }
    
    # Mock DB data
    mock_risk_trend = [
        {'run_id': 1, 'risk': 'low'},
        {'run_id': 2, 'risk': 'medium'},
        {'run_id': 3, 'risk': 'medium'}
    ]
    
    mock_compliance_trend = [
        {'run_id': 1, 'issue_count': 0},
        {'run_id': 2, 'issue_count': 1},
        {'run_id': 3, 'issue_count': 2}
    ]
    
    mock_escalation_counts = {
        'Monitor for recurring patterns': 5,
        'None required': 3
    }
    
    mock_category_distribution = {
        'security': 10,
        'network': 5
    }
    
    # Mock LLM to raise an exception
    with patch('agents.llm_governance_insights_agent.OpenAIClient') as MockClient, \
         patch('agents.llm_governance_insights_agent.db_util') as mock_db_util:
        
        mock_client_instance = Mock()
        mock_client_instance.generate.side_effect = Exception("LLM API error")
        MockClient.return_value = mock_client_instance
        
        # Mock DB utility functions
        mock_db_util.get_risk_trend.return_value = mock_risk_trend
        mock_db_util.get_compliance_trend.return_value = mock_compliance_trend
        mock_db_util.get_escalation_text_counts.return_value = mock_escalation_counts
        mock_db_util.get_recent_runs.return_value = []
        mock_db_util.get_category_distribution.return_value = mock_category_distribution
        mock_db_util.get_severity_distribution.return_value = {}
        
        agent = GovernanceInsightsAgent("GovernanceInsights")
        result = agent.run(sample_governance_output)
    
    # Should fall back to basic analysis
    assert 'governance_output' in result, "Should still return governance output"
    assert 'insights' in result, "Should provide fallback insights"
    
    insights = result['insights']
    assert 'trend_summary' in insights, "Fallback should have trend summary"
    assert 'recommendations' in insights, "Fallback should have recommendations"
    assert isinstance(insights['recommendations'], list), "Recommendations should be a list"
    assert len(insights['recommendations']) > 0, "Should have at least one recommendation"
    
    # Verify fallback analysis includes basic statistics
    assert 'medium' in insights['trend_summary'], "Should mention most common risk level"
    assert 'increasing' in insights['compliance_trend'], "Should detect increasing compliance issues"
    
    print("  ✓ Handles LLM failure gracefully")
    print("  ✓ Provides fallback analysis based on DB data")
    print(f"  ✓ Fallback trend summary: {insights['trend_summary']}")
    print(f"  ✓ Fallback recommendations: {len(insights['recommendations'])}")
    
    print("\n" + "="*60)
    print("✓ Fallback test passed")
    print("="*60)
    
    return result


if __name__ == "__main__":
    # Run all tests
    test_llm_governance_insights_agent()
    test_governance_insights_no_data()
    test_governance_insights_fallback()
    
    print("\n" + "="*60)
    print("ALL GOVERNANCE INSIGHTS AGENT TESTS PASSED ✓")
    print("="*60)
