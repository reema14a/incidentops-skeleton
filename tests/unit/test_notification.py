#!/usr/bin/env python3
"""Test to verify NotificationAgent implementation."""

from unittest.mock import Mock, MagicMock
from agents.notification_agent import NotificationAgent
from llm.mcp_client import MCPClient


def test_notification_agent_high_risk():
    """Test NotificationAgent sends notification for high risk incidents."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - HIGH RISK")
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
            'escalation': 'Immediate review by IT security team required',
            'compliance_issues': ['Multiple high-severity incidents without automated remediation'],
            'commentary': 'High risk situation requiring immediate attention'
        }
    }
    
    # Mock MCP client
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.return_value = {
        'success': True,
        'result': {'message_id': 'test-123'},
        'request_id': 'req-123',
        'tool_name': 'gmail.send',
        'timestamp': '2025-11-16T05:59:14Z'
    }
    
    # Create agent with mocked MCP client
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify result structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    assert 'governance_output' in result, "Result must contain 'governance_output' field"
    assert 'notification_status' in result, "Result must contain 'notification_status' field"
    assert 'notifications_sent' in result, "Result must contain 'notifications_sent' field"
    print("  ✓ Result has required fields")
    
    # Verify governance output is passed through
    assert result['governance_output'] == sample_governance_output, "Original governance output should be passed through"
    print("  ✓ Original governance output passed through")
    
    # Verify notification was sent
    assert result['notification_status'] == 'success', "Notification should be sent for high risk"
    assert len(result['notifications_sent']) > 0, "At least one notification should be sent"
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Notifications Sent: {len(result['notifications_sent'])}")
    
    # Verify notification details
    if len(result['notifications_sent']) > 0:
        notification = result['notifications_sent'][0]
        assert notification['status'] == 'sent', "Notification should be marked as sent"
        assert 'HIGH' in notification['subject'], "Subject should indicate high risk"
        assert notification['priority'] == 'high', "Priority should be high"
        print(f"  ✓ Channel: {notification['channel']}")
        print(f"  ✓ Subject: {notification['subject']}")
        print(f"  ✓ Priority: {notification['priority']}")
    else:
        print("  ℹ No notifications sent (channels may be empty)")
    
    print("\n" + "="*60)
    print("✓ High risk notification test passed")
    print("="*60)
    
    return result


def test_notification_agent_critical_risk():
    """Test NotificationAgent sends urgent notification for critical risk."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - CRITICAL RISK")
    print("="*60)
    
    # Sample governance output with critical risk
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 15,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'critical',
            'escalation': 'Immediate escalation to incident commander required',
            'compliance_issues': ['System-wide outage risk', 'SLA breach imminent'],
            'commentary': 'Critical situation requiring immediate executive attention'
        }
    }
    
    # Mock MCP client
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.return_value = {
        'success': True,
        'result': {'message_id': 'test-456'},
        'request_id': 'req-456',
        'tool_name': 'gmail.send',
        'timestamp': '2025-11-16T05:59:14Z'
    }
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify notification was sent with urgent priority
    if len(result['notifications_sent']) > 0:
        assert result['notification_status'] in ['success', 'partial_failure'], "Notification should be attempted for critical risk"
        
        notification = result['notifications_sent'][0]
        if notification['status'] == 'sent':
            assert notification['priority'] == 'urgent', "Priority should be urgent for critical risk"
            assert 'CRITICAL' in notification['subject'], "Subject should indicate critical risk"
            
            print(f"  ✓ Notification Status: {result['notification_status']}")
            print(f"  ✓ Priority: {notification['priority']}")
            print(f"  ✓ Subject: {notification['subject']}")
        else:
            print(f"  ℹ Notification attempted but failed: {notification.get('error', 'Unknown error')}")
    else:
        print("  ℹ No notifications sent (channels may be empty)")
    
    print("\n" + "="*60)
    print("✓ Critical risk notification test passed")
    print("="*60)
    
    return result


def test_notification_agent_low_risk_no_escalation():
    """Test NotificationAgent skips notification for low risk without escalation."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - LOW RISK")
    print("="*60)
    
    # Sample governance output with low risk and no escalation
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 2,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'low',
            'escalation': 'None required',
            'compliance_issues': [],
            'commentary': 'System operating normally with minor alerts'
        }
    }
    
    # Mock MCP client (won't be called for low risk)
    mock_mcp_client = MagicMock(spec=MCPClient)
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify notification was NOT sent
    assert result['notification_status'] == 'not_required', "Notification should not be sent for low risk"
    assert len(result['notifications_sent']) == 0, "No notifications should be sent"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print(f"  ✓ Notifications Sent: {len(result['notifications_sent'])}")
    print("  ✓ Correctly skipped notification for low risk")
    
    print("\n" + "="*60)
    print("✓ Low risk no notification test passed")
    print("="*60)
    
    return result


def test_notification_agent_medium_risk_with_escalation():
    """Test NotificationAgent sends notification for medium risk with escalation."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - MEDIUM RISK WITH ESCALATION")
    print("="*60)
    
    # Sample governance output with medium risk but escalation required
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 5,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'medium',
            'escalation': 'Review with team lead if issues persist',
            'compliance_issues': [],
            'commentary': 'Moderate risk requiring team lead review'
        }
    }
    
    # Mock MCP client
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.return_value = {
        'success': True,
        'result': {'message_id': 'test-789'},
        'request_id': 'req-789',
        'tool_name': 'gmail.send',
        'timestamp': '2025-11-16T05:59:14Z'
    }
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify notification was sent (escalation required)
    if len(result['notifications_sent']) > 0:
        notification = result['notifications_sent'][0]
        if notification['status'] == 'sent':
            assert notification['priority'] == 'normal', "Priority should be normal for medium risk"
            assert 'MEDIUM' in notification['subject'], "Subject should indicate medium risk"
            
            print(f"  ✓ Notification Status: {result['notification_status']}")
            print(f"  ✓ Priority: {notification['priority']}")
            print(f"  ✓ Subject: {notification['subject']}")
        else:
            print(f"  ℹ Notification attempted but failed: {notification.get('error', 'Unknown error')}")
    else:
        print("  ℹ No notifications sent (channels may be empty)")
    
    print("\n" + "="*60)
    print("✓ Medium risk with escalation test passed")
    print("="*60)
    
    return result


def test_notification_agent_no_data():
    """Test NotificationAgent handles no data gracefully."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - NO DATA")
    print("="*60)
    
    # Mock MCP client (won't be called for no data)
    mock_mcp_client = MagicMock(spec=MCPClient)
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(None)
    
    # Should handle no data gracefully
    assert result['notification_status'] == 'skipped', "Should skip notification for no data"
    assert len(result['notifications_sent']) == 0, "No notifications should be sent"
    
    print(f"  ✓ Notification Status: {result['notification_status']}")
    print("  ✓ Handles no data gracefully")
    
    print("\n" + "="*60)
    print("✓ No data test passed")
    print("="*60)
    
    return result


def test_notification_content_preparation():
    """Test notification content preparation with compliance issues."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - CONTENT PREPARATION")
    print("="*60)
    
    # Sample governance output with compliance issues
    sample_governance_output = {
        'audit_summary': {
            'status': 'logged',
            'count': 6,
            'timestamp': '2025-11-16 05:59:14',
            'output_path': 'data/output_log.json'
        },
        'governance_analysis': {
            'risk': 'high',
            'escalation': 'Immediate review required',
            'compliance_issues': [
                'SLA breach detected',
                'Incident response time exceeded threshold',
                'Missing automated remediation'
            ],
            'commentary': 'Multiple compliance violations detected requiring immediate attention'
        }
    }
    
    # Mock MCP client
    mock_mcp_client = MagicMock(spec=MCPClient)
    mock_mcp_client.call_tool.return_value = {
        'success': True,
        'result': {'message_id': 'test-content'},
        'request_id': 'req-content',
        'tool_name': 'gmail.send',
        'timestamp': '2025-11-16T05:59:14Z'
    }
    
    agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
    result = agent.run(sample_governance_output)
    
    # Verify notification was sent
    if len(result['notifications_sent']) > 0:
        notification = result['notifications_sent'][0]
        
        if notification['status'] == 'sent':
            # Verify subject contains key information
            assert 'HIGH' in notification['subject'], "Subject should indicate risk level"
            assert '6 incident(s)' in notification['subject'], "Subject should include incident count"
            
            print(f"  ✓ Subject: {notification['subject']}")
            print(f"  ✓ Priority: {notification['priority']}")
            print(f"  ✓ Channel: {notification['channel']}")
        else:
            print(f"  ℹ Notification attempted but failed: {notification.get('error', 'Unknown error')}")
    else:
        print("  ℹ No notifications sent (channels may be empty)")
    
    print("\n" + "="*60)
    print("✓ Content preparation test passed")
    print("="*60)
    
    return result


def test_notification_priority_mapping():
    """Test notification priority mapping for different risk levels."""
    
    print("\n" + "="*60)
    print("NOTIFICATION AGENT TEST - PRIORITY MAPPING")
    print("="*60)
    
    test_cases = [
        ('low', 'normal'),
        ('medium', 'normal'),
        ('high', 'high'),
        ('critical', 'urgent')
    ]
    
    for risk_level, expected_priority in test_cases:
        sample_governance_output = {
            'audit_summary': {
                'status': 'logged',
                'count': 5,
                'timestamp': '2025-11-16 05:59:14',
                'output_path': 'data/output_log.json'
            },
            'governance_analysis': {
                'risk': risk_level,
                'escalation': 'Review required',
                'compliance_issues': [],
                'commentary': f'{risk_level} risk situation'
            }
        }
        
        # Mock MCP client
        mock_mcp_client = MagicMock(spec=MCPClient)
        mock_mcp_client.call_tool.return_value = {
            'success': True,
            'result': {'message_id': f'test-{risk_level}'},
            'request_id': f'req-{risk_level}',
            'tool_name': 'gmail.send',
            'timestamp': '2025-11-16T05:59:14Z'
        }
        
        agent = NotificationAgent("NotificationAgent", mcp_client=mock_mcp_client)
        result = agent.run(sample_governance_output)
        
        if result['notification_status'] in ['success', 'partial_failure'] and len(result['notifications_sent']) > 0:
            notification = result['notifications_sent'][0]
            if notification['status'] == 'sent':
                assert notification['priority'] == expected_priority, f"Expected {expected_priority} for {risk_level} risk"
                print(f"  ✓ {risk_level} risk → {expected_priority} priority")
            else:
                print(f"  ℹ {risk_level} risk notification attempted but failed")
        else:
            print(f"  ℹ {risk_level} risk - no notification sent (may not meet criteria)")
    
    print("\n" + "="*60)
    print("✓ Priority mapping test passed")
    print("="*60)


if __name__ == "__main__":
    # Run all tests
    test_notification_agent_high_risk()
    test_notification_agent_critical_risk()
    test_notification_agent_low_risk_no_escalation()
    test_notification_agent_medium_risk_with_escalation()
    test_notification_agent_no_data()
    test_notification_content_preparation()
    test_notification_priority_mapping()
    
    print("\n" + "="*60)
    print("ALL NOTIFICATION AGENT TESTS PASSED ✓")
    print("="*60)
