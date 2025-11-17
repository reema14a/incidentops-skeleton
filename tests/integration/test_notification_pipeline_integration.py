#!/usr/bin/env python3
"""Integration test for NotificationAgent in the full pipeline.

This test verifies that NotificationAgent is properly integrated into the pipeline
and that MCP errors are handled gracefully without stopping the pipeline.
"""

from unittest.mock import Mock, patch, MagicMock
from orchestrator.orchestrator import PipelineExecutor
from llm.mcp_client import MCPToolError, MCPConnectionError, MCPTimeoutError


def test_notification_agent_mcp_error_does_not_stop_pipeline():
    """Test that MCP errors in NotificationAgent don't stop the pipeline."""
    
    print("\n" + "="*60)
    print("PIPELINE INTEGRATION TEST - NOTIFICATION MCP ERROR HANDLING")
    print("="*60)
    
    # Mock OpenAI client to avoid real API calls
    mock_openai_response = '{"summary": "Test summary", "categories": ["Test"], "severity_breakdown": {"ERROR": 1}, "root_causes": ["Test cause"]}'
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockOpenAI, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock all LLM agents
        mock_openai_instance = Mock()
        mock_openai_instance.generate.return_value = mock_openai_response
        MockOpenAI.return_value = mock_openai_instance
        MockResolution.return_value = mock_openai_instance
        
        # Mock governance response
        mock_governance_response = '{"risk": "high", "escalation": "Immediate review required", "compliance_issues": [], "commentary": "High risk detected"}'
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client to raise MCPToolError
        mock_mcp_client = MagicMock()
        mock_mcp_client.call_tool.side_effect = MCPToolError(
            "MCP tool failed",
            tool_name="gmail.send",
            request_id="test-123"
        )
        
        # Replace NotificationAgent's MCP client with mock
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline - should complete despite MCP error
        print("\nRunning pipeline with MCP error in NotificationAgent...")
        result = executor.run()
        
        # Verify pipeline completed
        assert result is not None, "Pipeline should return a result"
        print("  ✓ Pipeline completed successfully")
        
        # Verify NotificationAgent output structure
        assert 'governance_output' in result, "Result should contain governance_output"
        assert 'notification_status' in result, "Result should contain notification_status"
        assert 'notifications_sent' in result, "Result should contain notifications_sent"
        print("  ✓ NotificationAgent output structure is correct")
        
        # Verify notification failed gracefully
        assert result['notification_status'] in ['failed', 'partial_failure'], \
            "Notification status should indicate failure"
        print(f"  ✓ Notification status: {result['notification_status']}")
        
        # Verify error details are captured
        assert len(result['notifications_sent']) > 0, "Should have notification attempts"
        for notification in result['notifications_sent']:
            assert notification['status'] == 'failed', "Notifications should be marked as failed"
            assert 'error' in notification, "Should include error message"
            assert notification['error_type'] == 'MCPToolError', "Should identify error type"
        print(f"  ✓ Error details captured: {result['notifications_sent'][0]['error_type']}")
        
        # Verify governance output is preserved
        assert 'governance_analysis' in result['governance_output'], \
            "Governance analysis should be preserved"
        print("  ✓ Governance output preserved through NotificationAgent")
    
    print("\n" + "="*60)
    print("✓ Pipeline integration test passed")
    print("="*60)


def test_notification_agent_connection_error_does_not_stop_pipeline():
    """Test that MCP connection errors don't stop the pipeline."""
    
    print("\n" + "="*60)
    print("PIPELINE INTEGRATION TEST - NOTIFICATION CONNECTION ERROR")
    print("="*60)
    
    mock_openai_response = '{"summary": "Test", "categories": ["Test"], "severity_breakdown": {"ERROR": 1}, "root_causes": ["Test"]}'
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockOpenAI, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        mock_openai_instance = Mock()
        mock_openai_instance.generate.return_value = mock_openai_response
        MockOpenAI.return_value = mock_openai_instance
        MockResolution.return_value = mock_openai_instance
        
        mock_governance_response = '{"risk": "critical", "escalation": "Immediate", "compliance_issues": [], "commentary": "Critical"}'
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        executor = PipelineExecutor()
        
        # Mock MCP client to raise MCPConnectionError
        mock_mcp_client = MagicMock()
        mock_mcp_client.call_tool.side_effect = MCPConnectionError(
            "Connection failed",
            endpoint="https://mcp.example.com"
        )
        
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        print("\nRunning pipeline with MCP connection error...")
        result = executor.run()
        
        assert result is not None, "Pipeline should complete"
        assert result['notification_status'] in ['failed', 'partial_failure']
        assert all(n['error_type'] == 'MCPConnectionError' for n in result['notifications_sent'])
        
        print("  ✓ Pipeline completed despite connection error")
        print(f"  ✓ Error type: {result['notifications_sent'][0]['error_type']}")
    
    print("\n" + "="*60)
    print("✓ Connection error test passed")
    print("="*60)


def test_notification_agent_timeout_does_not_stop_pipeline():
    """Test that MCP timeout errors don't stop the pipeline."""
    
    print("\n" + "="*60)
    print("PIPELINE INTEGRATION TEST - NOTIFICATION TIMEOUT ERROR")
    print("="*60)
    
    mock_openai_response = '{"summary": "Test", "categories": ["Test"], "severity_breakdown": {"ERROR": 1}, "root_causes": ["Test"]}'
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockOpenAI, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        mock_openai_instance = Mock()
        mock_openai_instance.generate.return_value = mock_openai_response
        MockOpenAI.return_value = mock_openai_instance
        MockResolution.return_value = mock_openai_instance
        
        mock_governance_response = '{"risk": "high", "escalation": "Review", "compliance_issues": [], "commentary": "High risk"}'
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        executor = PipelineExecutor()
        
        # Mock MCP client to raise MCPTimeoutError
        mock_mcp_client = MagicMock()
        mock_mcp_client.call_tool.side_effect = MCPTimeoutError(
            "Request timed out",
            timeout_seconds=30.0,
            operation="tool_call"
        )
        
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        print("\nRunning pipeline with MCP timeout error...")
        result = executor.run()
        
        assert result is not None, "Pipeline should complete"
        assert result['notification_status'] in ['failed', 'partial_failure']
        assert all(n['error_type'] == 'MCPTimeoutError' for n in result['notifications_sent'])
        
        print("  ✓ Pipeline completed despite timeout error")
        print(f"  ✓ Error type: {result['notifications_sent'][0]['error_type']}")
    
    print("\n" + "="*60)
    print("✓ Timeout error test passed")
    print("="*60)


if __name__ == "__main__":
    test_notification_agent_mcp_error_does_not_stop_pipeline()
    test_notification_agent_connection_error_does_not_stop_pipeline()
    test_notification_agent_timeout_does_not_stop_pipeline()
    
    print("\n" + "="*60)
    print("ALL PIPELINE INTEGRATION TESTS PASSED ✓")
    print("="*60)
