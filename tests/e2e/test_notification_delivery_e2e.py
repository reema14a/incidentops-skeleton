#!/usr/bin/env python3
"""End-to-end test for notification delivery through the full pipeline.

This test verifies that notifications are successfully delivered through
the MCP client when the pipeline runs with high-risk incidents.
"""

from unittest.mock import Mock, patch, MagicMock
from orchestrator.orchestrator import PipelineExecutor


def test_notification_delivery_success_high_risk():
    """Test successful notification delivery for high-risk incidents through full pipeline."""
    
    print("\n" + "="*60)
    print("E2E TEST - SUCCESSFUL NOTIFICATION DELIVERY (HIGH RISK)")
    print("="*60)
    
    # Mock OpenAI responses for all LLM agents
    mock_summary_response = '''{
        "summary": "Critical database connection failures detected",
        "categories": ["Database", "Connection"],
        "severity_breakdown": {"CRITICAL": 3, "ERROR": 5},
        "root_causes": ["Database connection pool exhausted", "Network timeout"]
    }'''
    
    mock_resolution_response = '''{
        "resolution_summary": "Restart database connection pool and increase timeout",
        "top_actions": ["Restart service", "Increase connection pool size"]
    }'''
    
    mock_governance_response = '''{
        "risk": "high",
        "escalation": "Immediate review by database team required",
        "compliance_issues": ["SLA breach detected", "Response time exceeded"],
        "commentary": "High risk situation with multiple critical database failures requiring immediate attention"
    }'''
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockSummary, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock LLM agents
        mock_summary_instance = Mock()
        mock_summary_instance.generate.return_value = mock_summary_response
        MockSummary.return_value = mock_summary_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.generate.return_value = mock_resolution_response
        MockResolution.return_value = mock_resolution_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client to simulate successful notification delivery
        mock_mcp_client = MagicMock()
        
        # Simulate successful gmail.send call
        mock_mcp_client.call_tool.return_value = {
            'success': True,
            'result': {
                'message_id': 'msg-12345',
                'status': 'sent',
                'timestamp': '2025-11-17T10:30:00Z'
            },
            'request_id': 'req-67890',
            'tool_name': 'gmail.send',
            'timestamp': '2025-11-17T10:30:00Z'
        }
        
        # Replace NotificationAgent's MCP client with mock
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline
        print("\nRunning full pipeline with high-risk incident...")
        result = executor.run()
        
        # Verify pipeline completed successfully
        assert result is not None, "Pipeline should return a result"
        print("  ✓ Pipeline completed successfully")
        
        # Verify result structure
        assert 'governance_output' in result, "Result should contain governance_output"
        assert 'notification_status' in result, "Result should contain notification_status"
        assert 'notifications_sent' in result, "Result should contain notifications_sent"
        print("  ✓ Result structure is correct")
        
        # Verify governance analysis
        governance = result['governance_output']['governance_analysis']
        assert governance['risk'] == 'high', "Risk level should be high"
        assert 'Immediate review' in governance['escalation'], "Should require escalation"
        print(f"  ✓ Risk Level: {governance['risk']}")
        print(f"  ✓ Escalation: {governance['escalation']}")
        
        # Verify notification was sent successfully
        assert result['notification_status'] == 'success', \
            "Notification status should be success"
        print(f"  ✓ Notification Status: {result['notification_status']}")
        
        # Verify notification details
        assert len(result['notifications_sent']) > 0, \
            "Should have at least one notification sent"
        
        notification = result['notifications_sent'][0]
        assert notification['status'] == 'sent', "Notification should be marked as sent"
        assert notification['channel'] == 'gmail', "Should use gmail channel"
        assert 'HIGH' in notification['subject'], "Subject should indicate high risk"
        assert notification['priority'] == 'high', "Priority should be high"
        assert 'mcp_result' in notification, "Should include MCP result"
        assert 'request_id' in notification, "Should include request ID"
        
        print(f"  ✓ Channel: {notification['channel']}")
        print(f"  ✓ Subject: {notification['subject']}")
        print(f"  ✓ Priority: {notification['priority']}")
        print(f"  ✓ Request ID: {notification['request_id']}")
        
        # Verify MCP client was called with correct parameters
        assert mock_mcp_client.call_tool.called, "MCP client should be called"
        
        # Check all calls (may be multiple channels)
        all_calls = mock_mcp_client.call_tool.call_args_list
        assert len(all_calls) > 0, "Should have at least one MCP call"
        
        # Find the gmail call
        gmail_call = None
        for call in all_calls:
            if call[0][0] == 'gmail.send':
                gmail_call = call
                break
        
        assert gmail_call is not None, "Should have called gmail.send tool"
        
        params = gmail_call[0][1]
        assert 'to' in params, "Should include recipient"
        assert 'subject' in params, "Should include subject"
        assert 'body' in params, "Should include body"
        assert 'HIGH' in params['subject'], "Subject should indicate high risk"
        
        print(f"  ✓ MCP Tool Called: gmail.send")
        print(f"  ✓ Recipient: {params['to']}")
        print(f"  ✓ Total MCP Calls: {len(all_calls)}")
    
    print("\n" + "="*60)
    print("✓ E2E notification delivery test passed")
    print("="*60)


def test_notification_delivery_success_critical_risk():
    """Test successful notification delivery for critical-risk incidents with urgent priority."""
    
    print("\n" + "="*60)
    print("E2E TEST - SUCCESSFUL NOTIFICATION DELIVERY (CRITICAL RISK)")
    print("="*60)
    
    # Mock OpenAI responses for critical situation
    mock_summary_response = '''{
        "summary": "System-wide outage detected across all services",
        "categories": ["System", "Outage", "Critical"],
        "severity_breakdown": {"CRITICAL": 10},
        "root_causes": ["Infrastructure failure", "Network partition"]
    }'''
    
    mock_resolution_response = '''{
        "resolution_summary": "Emergency failover to backup datacenter required",
        "top_actions": ["Initiate failover", "Alert incident commander"]
    }'''
    
    mock_governance_response = '''{
        "risk": "critical",
        "escalation": "Immediate escalation to incident commander and executive team",
        "compliance_issues": ["System-wide outage", "SLA breach imminent", "Revenue impact"],
        "commentary": "Critical system-wide failure requiring immediate executive attention and emergency response"
    }'''
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockSummary, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock LLM agents
        mock_summary_instance = Mock()
        mock_summary_instance.generate.return_value = mock_summary_response
        MockSummary.return_value = mock_summary_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.generate.return_value = mock_resolution_response
        MockResolution.return_value = mock_resolution_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client for successful delivery
        mock_mcp_client = MagicMock()
        mock_mcp_client.call_tool.return_value = {
            'success': True,
            'result': {
                'message_id': 'msg-critical-999',
                'status': 'sent',
                'timestamp': '2025-11-17T10:35:00Z'
            },
            'request_id': 'req-critical-999',
            'tool_name': 'gmail.send',
            'timestamp': '2025-11-17T10:35:00Z'
        }
        
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline
        print("\nRunning full pipeline with critical-risk incident...")
        result = executor.run()
        
        # Verify critical risk handling
        governance = result['governance_output']['governance_analysis']
        assert governance['risk'] == 'critical', "Risk level should be critical"
        print(f"  ✓ Risk Level: {governance['risk']}")
        
        # Verify urgent notification was sent
        assert result['notification_status'] == 'success', \
            "Notification should be sent successfully"
        
        notification = result['notifications_sent'][0]
        assert notification['status'] == 'sent', "Notification should be sent"
        assert notification['priority'] == 'urgent', "Priority should be urgent for critical risk"
        assert 'CRITICAL' in notification['subject'], "Subject should indicate critical risk"
        
        print(f"  ✓ Notification Status: {result['notification_status']}")
        print(f"  ✓ Priority: {notification['priority']}")
        print(f"  ✓ Subject: {notification['subject']}")
    
    print("\n" + "="*60)
    print("✓ E2E critical notification delivery test passed")
    print("="*60)


def test_notification_delivery_multi_channel():
    """Test notification delivery across multiple channels (gmail and pushover)."""
    
    print("\n" + "="*60)
    print("E2E TEST - MULTI-CHANNEL NOTIFICATION DELIVERY")
    print("="*60)
    
    # Mock OpenAI responses
    mock_summary_response = '''{
        "summary": "High-priority security incident detected",
        "categories": ["Security", "Breach"],
        "severity_breakdown": {"CRITICAL": 2, "ERROR": 3},
        "root_causes": ["Unauthorized access attempt"]
    }'''
    
    mock_resolution_response = '''{
        "resolution_summary": "Block suspicious IP and review access logs",
        "top_actions": ["Block IP", "Review logs", "Alert security team"]
    }'''
    
    mock_governance_response = '''{
        "risk": "high",
        "escalation": "Immediate security team review required",
        "compliance_issues": ["Security breach attempt"],
        "commentary": "High-priority security incident requiring immediate attention"
    }'''
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockSummary, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock LLM agents
        mock_summary_instance = Mock()
        mock_summary_instance.generate.return_value = mock_summary_response
        MockSummary.return_value = mock_summary_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.generate.return_value = mock_resolution_response
        MockResolution.return_value = mock_resolution_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client to simulate successful delivery on both channels
        mock_mcp_client = MagicMock()
        
        # Return different responses for gmail and pushover
        mock_mcp_client.call_tool.side_effect = [
            # Gmail response
            {
                'success': True,
                'result': {'message_id': 'gmail-msg-123'},
                'request_id': 'gmail-req-123',
                'tool_name': 'gmail.send',
                'timestamp': '2025-11-17T10:40:00Z'
            },
            # Pushover response
            {
                'success': True,
                'result': {'message_id': 'pushover-msg-456'},
                'request_id': 'pushover-req-456',
                'tool_name': 'pushover.send',
                'timestamp': '2025-11-17T10:40:01Z'
            }
        ]
        
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline
        print("\nRunning full pipeline with multi-channel notifications...")
        result = executor.run()
        
        # Verify both notifications were sent
        assert result['notification_status'] == 'success', \
            "Both notifications should be sent successfully"
        
        assert len(result['notifications_sent']) == 2, \
            "Should have 2 notifications (gmail and pushover)"
        
        # Verify gmail notification
        gmail_notification = result['notifications_sent'][0]
        assert gmail_notification['status'] == 'sent', "Gmail notification should be sent"
        assert gmail_notification['channel'] == 'gmail', "First should be gmail"
        print(f"  ✓ Gmail notification sent: {gmail_notification['request_id']}")
        
        # Verify pushover notification
        pushover_notification = result['notifications_sent'][1]
        assert pushover_notification['status'] == 'sent', "Pushover notification should be sent"
        assert pushover_notification['channel'] == 'pushover', "Second should be pushover"
        print(f"  ✓ Pushover notification sent: {pushover_notification['request_id']}")
        
        # Verify MCP client was called twice
        assert mock_mcp_client.call_tool.call_count == 2, \
            "MCP client should be called twice (once per channel)"
        
        print(f"  ✓ Notification Status: {result['notification_status']}")
        print(f"  ✓ Total Notifications Sent: {len(result['notifications_sent'])}")
    
    print("\n" + "="*60)
    print("✓ E2E multi-channel notification delivery test passed")
    print("="*60)


def test_notification_not_sent_for_low_risk():
    """Test that notifications are NOT sent for low-risk incidents."""
    
    print("\n" + "="*60)
    print("E2E TEST - NO NOTIFICATION FOR LOW RISK")
    print("="*60)
    
    # Mock OpenAI responses for low-risk situation
    mock_summary_response = '''{
        "summary": "Minor informational alerts detected",
        "categories": ["Info"],
        "severity_breakdown": {"INFO": 2},
        "root_causes": ["Normal system activity"]
    }'''
    
    mock_resolution_response = '''{
        "resolution_summary": "No action required",
        "top_actions": ["Monitor"]
    }'''
    
    mock_governance_response = '''{
        "risk": "low",
        "escalation": "None required",
        "compliance_issues": [],
        "commentary": "System operating normally with minor informational alerts"
    }'''
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockSummary, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock LLM agents
        mock_summary_instance = Mock()
        mock_summary_instance.generate.return_value = mock_summary_response
        MockSummary.return_value = mock_summary_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.generate.return_value = mock_resolution_response
        MockResolution.return_value = mock_resolution_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client (should NOT be called for low risk)
        mock_mcp_client = MagicMock()
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline
        print("\nRunning full pipeline with low-risk incident...")
        result = executor.run()
        
        # Verify low risk
        governance = result['governance_output']['governance_analysis']
        assert governance['risk'] == 'low', "Risk level should be low"
        print(f"  ✓ Risk Level: {governance['risk']}")
        
        # Verify notification was NOT sent
        assert result['notification_status'] == 'not_required', \
            "Notification should not be required for low risk"
        
        assert len(result['notifications_sent']) == 0, \
            "No notifications should be sent for low risk"
        
        # Verify MCP client was NOT called
        assert not mock_mcp_client.call_tool.called, \
            "MCP client should not be called for low risk"
        
        print(f"  ✓ Notification Status: {result['notification_status']}")
        print(f"  ✓ Notifications Sent: {len(result['notifications_sent'])}")
        print("  ✓ Correctly skipped notification for low risk")
    
    print("\n" + "="*60)
    print("✓ E2E low-risk no notification test passed")
    print("="*60)


def test_notification_content_includes_compliance_issues():
    """Test that notification content includes compliance issues when present."""
    
    print("\n" + "="*60)
    print("E2E TEST - NOTIFICATION CONTENT WITH COMPLIANCE ISSUES")
    print("="*60)
    
    # Mock OpenAI responses with compliance issues
    mock_summary_response = '''{
        "summary": "SLA breach and compliance violations detected",
        "categories": ["Compliance", "SLA"],
        "severity_breakdown": {"ERROR": 5},
        "root_causes": ["Response time exceeded", "Automated remediation failed"]
    }'''
    
    mock_resolution_response = '''{
        "resolution_summary": "Review SLA policies and improve automation",
        "top_actions": ["Review SLA", "Improve automation"]
    }'''
    
    mock_governance_response = '''{
        "risk": "high",
        "escalation": "Immediate compliance review required",
        "compliance_issues": [
            "SLA breach detected",
            "Response time exceeded threshold",
            "Missing automated remediation"
        ],
        "commentary": "Multiple compliance violations requiring immediate attention"
    }'''
    
    with patch('agents.llm_alert_summary_agent.OpenAIClient') as MockSummary, \
         patch('agents.llm_resolution_agent.OpenAIClient') as MockResolution, \
         patch('agents.llm_governance_agent.OpenAIClient') as MockGovernance:
        
        # Mock LLM agents
        mock_summary_instance = Mock()
        mock_summary_instance.generate.return_value = mock_summary_response
        MockSummary.return_value = mock_summary_instance
        
        mock_resolution_instance = Mock()
        mock_resolution_instance.generate.return_value = mock_resolution_response
        MockResolution.return_value = mock_resolution_instance
        
        mock_governance_instance = Mock()
        mock_governance_instance.generate.return_value = mock_governance_response
        MockGovernance.return_value = mock_governance_instance
        
        # Create executor
        executor = PipelineExecutor()
        
        # Mock MCP client
        mock_mcp_client = MagicMock()
        mock_mcp_client.call_tool.return_value = {
            'success': True,
            'result': {'message_id': 'msg-compliance-123'},
            'request_id': 'req-compliance-123',
            'tool_name': 'gmail.send',
            'timestamp': '2025-11-17T10:45:00Z'
        }
        
        executor.agents['notification'].mcp_client = mock_mcp_client
        
        # Run pipeline
        print("\nRunning full pipeline with compliance issues...")
        result = executor.run()
        
        # Verify notification was sent
        assert result['notification_status'] == 'success', \
            "Notification should be sent for compliance issues"
        
        notification = result['notifications_sent'][0]
        assert notification['status'] == 'sent', "Notification should be sent"
        
        # Verify MCP client was called with correct parameters
        all_calls = mock_mcp_client.call_tool.call_args_list
        assert len(all_calls) > 0, "Should have at least one MCP call"
        
        # Find the gmail call (which has 'body' parameter)
        gmail_call = None
        for call in all_calls:
            if call[0][0] == 'gmail.send':
                gmail_call = call
                break
        
        assert gmail_call is not None, "Should have called gmail.send tool"
        params = gmail_call[0][1]
        
        # Verify compliance issues are included in the body
        body = params['body']
        assert 'Compliance Issues:' in body, "Body should include compliance issues section"
        assert 'SLA breach detected' in body, "Body should include specific compliance issue"
        assert 'Response time exceeded threshold' in body, "Body should include all compliance issues"
        
        print(f"  ✓ Notification Status: {result['notification_status']}")
        print(f"  ✓ Subject: {notification['subject']}")
        print("  ✓ Compliance issues included in notification body")
    
    print("\n" + "="*60)
    print("✓ E2E notification content test passed")
    print("="*60)


if __name__ == "__main__":
    # Run all E2E tests
    test_notification_delivery_success_high_risk()
    test_notification_delivery_success_critical_risk()
    test_notification_delivery_multi_channel()
    test_notification_not_sent_for_low_risk()
    test_notification_content_includes_compliance_issues()
    
    print("\n" + "="*60)
    print("ALL E2E NOTIFICATION DELIVERY TESTS PASSED ✓")
    print("="*60)
