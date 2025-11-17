#!/usr/bin/env python3
"""Test NotificationAgent MCP error handling."""

from unittest.mock import MagicMock
from agents.notification_agent import NotificationAgent
from llm.mcp_client import MCPClient, MCPToolError, MCPConnectionError, MCPTimeoutError


def test_notification_agent_handles_mcp_tool_error():
    """Test NotificationAgent gracefully handles MCPToolError without stopping pipeline."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - MCP TOOL ERROR HANDLING")
    print("="*60)
    
    # Sample governance output with high risk
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 8,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'high',
            'escalation': 'Immediate review required',
            'compliance_issues': [],
            'commentary': 'High risk situation'
        }
    }
    
    # Mock MCP client to raise MCPToolError
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.side_effect = MCPToolError(
        "Tool invocation failed",
        tool_name="gmail.send",
        request_id="req-123"
    )
    
    # Create agent with mocked MCP client
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify agent handled error gracefully
    assert 'governance_output' in result, "Result must contain governance_output"
    assert 'notification_status' in result, "Result must contain notification_status"
    assert 'notifications_sent' in result, "Result must contain notifications_sent"
    
    # Should have partial_failure or failed status
    assert result['notification_status'] in ['partial_failure', 'failed'], \
        "Should indicate failure when MCP tool errors occur"
    
    # Should have error details in notifications_sent
    assert len(result['notifications_sent']) > 0, "Should record failed notification attempts"
    
    for notification in result['notifications_sent']:
        assert notification['status'] == 'failed', "Notification should be marked as failed"
        assert 'error' in notification, "Should include error message"
        assert notification['error_type'] == 'MCPToolError', "Should identify error type"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Failed Notifications: {len(result['notifications_sent'])}")
    print(f"  ✓ Error Type: {result['notifications_sent'][0]['error_type']}")
    print("  ✓ Pipeline continued despite MCP error")
    
    print("\n" + "="*60)
    print("✓ MCP tool error handling test passed")
    print("="*60)


def test_notification_agent_handles_mcp_connection_error():
    """Test NotificationAgent gracefully handles MCPConnectionError."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - MCP CONNECTION ERROR HANDLING")
    print("="*60)
    
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 5,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'critical',
            'escalation': 'Immediate escalation required',
            'compliance_issues': [],
            'commentary': 'Critical situation'
        }
    }
    
    # Mock MCP client to raise MCPConnectionError
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.side_effect = MCPConnectionError(
        "Failed to connect to MCP server",
        endpoint="https://mcp.example.com"
    )
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify graceful handling
    assert result['notification_status'] in ['partial_failure', 'failed'], \
        "Should indicate failure when connection errors occur"
    
    assert len(result['notifications_sent']) > 0, "Should record failed attempts"
    
    for notification in result['notifications_sent']:
        assert notification['status'] == 'failed', "Should mark as failed"
        assert notification['error_type'] == 'MCPConnectionError', "Should identify error type"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Error Type: {result['notifications_sent'][0]['error_type']}")
    print("  ✓ Pipeline continued despite connection error")
    
    print("\n" + "="*60)
    print("✓ MCP connection error handling test passed")
    print("="*60)


def test_notification_agent_handles_mcp_timeout_error():
    """Test NotificationAgent gracefully handles MCPTimeoutError."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - MCP TIMEOUT ERROR HANDLING")
    print("="*60)
    
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 3,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'high',
            'escalation': 'Review required',
            'compliance_issues': [],
            'commentary': 'High risk'
        }
    }
    
    # Mock MCP client to raise MCPTimeoutError
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.side_effect = MCPTimeoutError(
        "Request timed out",
        timeout_seconds=30.0,
        operation="tool_call"
    )
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify graceful handling
    assert result['notification_status'] in ['partial_failure', 'failed'], \
        "Should indicate failure when timeout occurs"
    
    assert len(result['notifications_sent']) > 0, "Should record failed attempts"
    
    for notification in result['notifications_sent']:
        assert notification['status'] == 'failed', "Should mark as failed"
        assert notification['error_type'] == 'MCPTimeoutError', "Should identify error type"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Error Type: {result['notifications_sent'][0]['error_type']}")
    print("  ✓ Pipeline continued despite timeout error")
    
    print("\n" + "="*60)
    print("✓ MCP timeout error handling test passed")
    print("="*60)


def test_notification_agent_partial_success():
    """Test NotificationAgent handles partial success (one channel succeeds, one fails)."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - PARTIAL SUCCESS")
    print("="*60)
    
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 7,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'high',
            'escalation': 'Immediate review required',
            'compliance_issues': [],
            'commentary': 'High risk situation'
        }
    }
    
    # Mock MCP client to succeed on first call, fail on second
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.side_effect = [
        # First call (gmail) succeeds
        {
            'success': True,
            'result': {'message_id': 'test-123'},
            'request_id': 'req-123',
            'tool_name': 'gmail.send',
            'timestamp': '2025-11-16T05:59:14Z'
        },
        # Second call (pushover) fails
        MCPToolError(
            "Pushover API error",
            tool_name="pushover.send",
            request_id="req-456"
        )
    ]
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify partial success
    assert result['notification_status'] == 'partial_failure', \
        "Should indicate partial_failure when some channels fail"
    
    assert len(result['notifications_sent']) == 2, "Should have 2 notification attempts"
    
    # First notification should succeed
    assert result['notifications_sent'][0]['status'] == 'sent', "First notification should succeed"
    assert result['notifications_sent'][0]['channel'] == 'gmail', "First should be gmail"
    
    # Second notification should fail
    assert result['notifications_sent'][1]['status'] == 'failed', "Second notification should fail"
    assert result['notifications_sent'][1]['channel'] == 'pushover', "Second should be pushover"
    assert result['notifications_sent'][1]['error_type'] == 'MCPToolError', "Should identify error type"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Successful: {result['notifications_sent'][0]['channel']}")
    print(f"  ✓ Failed: {result['notifications_sent'][1]['channel']}")
    print("  ✓ Partial success handled correctly")
    
    print("\n" + "="*60)
    print("✓ Partial success test passed")
    print("="*60)


if __name__ == "__main__":
    # Run all tests
    test_notification_agent_handles_mcp_tool_error()
    test_notification_agent_handles_mcp_connection_error()
    test_notification_agent_handles_mcp_timeout_error()
    test_notification_agent_partial_success()
    
    print("\n" + "="*60)
    print("ALL MCP ERROR HANDLING TESTS PASSED ✓")
    print("="*60)
