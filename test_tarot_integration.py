"""
Quick verification test for tarot integration in GovernanceInsightsAgent.
"""
from unittest.mock import Mock, patch
from agents.llm_governance_insights_agent import GovernanceInsightsAgent


def test_tarot_integration():
    """Test that tarot card is drawn and included in insights."""
    
    # Mock the MCP client
    mock_mcp_client = Mock()
    mock_mcp_client.call_tool.return_value = {
        'success': True,
        'result': {
            'card_name': 'The Tower',
            'meaning': 'Sudden change, upheaval',
            'risk_alignment': 'disruption',
            'omen_message': 'Beware of cascading failures'
        }
    }
    
    # Mock the LLM client
    mock_llm_response = '''
    {
        "trend_summary": "Test summary",
        "risk_trend": "Stable",
        "compliance_trend": "Improving",
        "recurring_issues": [],
        "category_hotspots": [],
        "recommendations": ["Test recommendation"],
        "anomaly_detection": "None detected"
    }
    '''
    
    with patch('agents.llm_governance_insights_agent.MCPClient') as MockMCPClient, \
         patch('agents.llm_governance_insights_agent.OpenAIClient') as MockOpenAIClient, \
         patch('agents.llm_governance_insights_agent.db_util') as mock_db:
        
        # Setup mocks
        MockMCPClient.return_value = mock_mcp_client
        mock_llm_client = Mock()
        mock_llm_client.generate.return_value = mock_llm_response
        MockOpenAIClient.return_value = mock_llm_client
        
        # Mock database to return data
        mock_db.get_risk_trend.return_value = [{'risk': 'medium', 'timestamp': '2024-01-01'}]
        mock_db.get_compliance_trend.return_value = [{'issue_count': 2, 'timestamp': '2024-01-01'}]
        mock_db.get_escalation_text_counts.return_value = {'escalate': 1}
        mock_db.get_recent_runs.return_value = [{'run_id': '123', 'timestamp': '2024-01-01', 'alerts_count': 5}]
        mock_db.get_category_distribution.return_value = {'error': 3}
        mock_db.get_severity_distribution.return_value = {'high': 2}
        
        # Create agent and run
        agent = GovernanceInsightsAgent()
        result = agent.run({'test': 'data'})
        
        # Verify tarot card was drawn
        mock_mcp_client.call_tool.assert_called_once_with('tarot.draw', {})
        
        # Verify tarot card is in insights
        assert 'insights' in result
        assert 'shadow_risk_interpretation' in result['insights']
        assert result['insights']['shadow_risk_interpretation'] is not None
        assert result['insights']['shadow_risk_interpretation']['card_name'] == 'The Tower'
        assert result['insights']['shadow_risk_interpretation']['risk_alignment'] == 'disruption'
        
        print("✅ Tarot integration test passed!")
        print(f"🔮 Tarot card: {result['insights']['shadow_risk_interpretation']['card_name']}")
        print(f"📊 Risk alignment: {result['insights']['shadow_risk_interpretation']['risk_alignment']}")


def test_tarot_graceful_failure():
    """Test that agent continues working when tarot fails."""
    
    # Mock the MCP client to fail
    mock_mcp_client = Mock()
    mock_mcp_client.call_tool.side_effect = Exception("MCP unavailable")
    
    # Mock the LLM client
    mock_llm_response = '''
    {
        "trend_summary": "Test summary",
        "risk_trend": "Stable",
        "compliance_trend": "Improving",
        "recurring_issues": [],
        "category_hotspots": [],
        "recommendations": ["Test recommendation"],
        "anomaly_detection": "None detected"
    }
    '''
    
    with patch('agents.llm_governance_insights_agent.MCPClient') as MockMCPClient, \
         patch('agents.llm_governance_insights_agent.OpenAIClient') as MockOpenAIClient, \
         patch('agents.llm_governance_insights_agent.db_util') as mock_db:
        
        # Setup mocks
        MockMCPClient.return_value = mock_mcp_client
        mock_llm_client = Mock()
        mock_llm_client.generate.return_value = mock_llm_response
        MockOpenAIClient.return_value = mock_llm_client
        
        # Mock database to return data
        mock_db.get_risk_trend.return_value = [{'risk': 'medium', 'timestamp': '2024-01-01'}]
        mock_db.get_compliance_trend.return_value = [{'issue_count': 2, 'timestamp': '2024-01-01'}]
        mock_db.get_escalation_text_counts.return_value = {'escalate': 1}
        mock_db.get_recent_runs.return_value = [{'run_id': '123', 'timestamp': '2024-01-01', 'alerts_count': 5}]
        mock_db.get_category_distribution.return_value = {'error': 3}
        mock_db.get_severity_distribution.return_value = {'high': 2}
        
        # Create agent and run
        agent = GovernanceInsightsAgent()
        result = agent.run({'test': 'data'})
        
        # Verify agent still works
        assert 'insights' in result
        assert 'shadow_risk_interpretation' in result['insights']
        # Should be None when tarot fails
        assert result['insights']['shadow_risk_interpretation'] is None
        
        # Verify other insights are still present
        assert result['insights']['trend_summary'] == "Test summary"
        
        print("✅ Graceful failure test passed!")
        print("🔮 Tarot unavailable, but insights still generated")


if __name__ == '__main__':
    test_tarot_integration()
    test_tarot_graceful_failure()
    print("\n✅ All tarot integration tests passed!")
