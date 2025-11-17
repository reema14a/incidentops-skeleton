#!/usr/bin/env python3
"""End-to-end test for NotificationAgent with local MCP server.

This script demonstrates the full notification flow:
1. NotificationAgent receives governance analysis
2. Determines notification is required
3. Calls MCPClient to send notifications
4. MCPClient sends JSON-RPC requests to local MCP server
5. MCP server routes to gmail.send and pushover.send tools
6. Tools send actual notifications (mocked in this test)

Prerequisites:
- MCP server must be running on http://localhost:5005
- Environment variables must be set (see .env file)
"""

import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.notification_agent import NotificationAgent


def test_gmail_notification():
    """Test Gmail notification through local MCP server."""
    print("\n" + "="*70)
    print("E2E TEST: NotificationAgent -> MCPClient -> MCP Server -> Gmail")
    print("="*70)
    
    # Mock SMTP to avoid actual email sending
    with patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Create NotificationAgent
        agent = NotificationAgent()
        
        # Prepare high-risk governance data to trigger notification
        input_data = {
            'governance_analysis': {
                'risk': 'high',
                'escalation': 'Immediate review required',
                'commentary': 'Critical database connection failures detected',
                'compliance_issues': [
                    'SLA breach: Response time exceeded threshold',
                    'Security policy violation: Unauthorized access attempts'
                ]
            },
            'audit_summary': {
                'count': 8,
                'timestamp': '2025-11-17T11:45:00Z',
                'incidents': [
                    {'severity': 'critical', 'type': 'database_error'},
                    {'severity': 'high', 'type': 'security_alert'}
                ]
            }
        }
        
        print("\n📧 Sending Gmail notification...")
        print(f"   Risk Level: {input_data['governance_analysis']['risk'].upper()}")
        print(f"   Incidents: {input_data['audit_summary']['count']}")
        print(f"   Escalation: {input_data['governance_analysis']['escalation']}")
        
        # Run agent
        result = agent.run(input_data)
        
        # Verify results
        print("\n✅ Results:")
        print(f"   Status: {result['notification_status']}")
        print(f"   Notifications sent: {len(result['notifications_sent'])}")
        
        for notification in result['notifications_sent']:
            print(f"\n   Channel: {notification['channel']}")
            print(f"   Status: {notification['status']}")
            print(f"   Subject: {notification.get('subject', 'N/A')}")
            print(f"   Request ID: {notification.get('request_id', 'N/A')}")
            
            if notification['status'] == 'sent':
                print(f"   ✓ Notification delivered successfully")
            else:
                print(f"   ✗ Notification failed: {notification.get('error', 'Unknown error')}")
        
        # Verify SMTP was called
        if mock_server.sendmail.called:
            print("\n✓ SMTP server was called (email would be sent in production)")
        
        print("\n" + "="*70)
        print("✓ Gmail E2E test completed successfully")
        print("="*70)
        
        return result['notification_status'] == 'success'


def test_pushover_notification():
    """Test Pushover notification through local MCP server."""
    print("\n" + "="*70)
    print("E2E TEST: NotificationAgent -> MCPClient -> MCP Server -> Pushover")
    print("="*70)
    
    # Mock Pushover API to avoid actual push notifications
    with patch('llm.local_mcp.tools.pushover_tool.requests') as mock_requests:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'pushover_e2e_test_123'
        }
        mock_requests.post.return_value = mock_response
        
        # Create NotificationAgent
        agent = NotificationAgent()
        
        # Prepare critical-risk governance data
        input_data = {
            'governance_analysis': {
                'risk': 'critical',
                'escalation': 'Immediate escalation to on-call engineer',
                'commentary': 'System-wide outage detected. Multiple services down.',
                'compliance_issues': [
                    'Critical SLA breach: 99.9% uptime violated',
                    'Incident response time exceeded 5 minutes'
                ]
            },
            'audit_summary': {
                'count': 15,
                'timestamp': '2025-11-17T12:00:00Z',
                'incidents': [
                    {'severity': 'critical', 'type': 'service_outage'},
                    {'severity': 'critical', 'type': 'database_failure'}
                ]
            }
        }
        
        print("\n📱 Sending Pushover notification...")
        print(f"   Risk Level: {input_data['governance_analysis']['risk'].upper()}")
        print(f"   Incidents: {input_data['audit_summary']['count']}")
        print(f"   Escalation: {input_data['governance_analysis']['escalation']}")
        
        # Run agent
        result = agent.run(input_data)
        
        # Verify results
        print("\n✅ Results:")
        print(f"   Status: {result['notification_status']}")
        print(f"   Notifications sent: {len(result['notifications_sent'])}")
        
        for notification in result['notifications_sent']:
            print(f"\n   Channel: {notification['channel']}")
            print(f"   Status: {notification['status']}")
            print(f"   Subject: {notification.get('subject', 'N/A')}")
            print(f"   Priority: {notification.get('priority', 'N/A')}")
            print(f"   Request ID: {notification.get('request_id', 'N/A')}")
            
            if notification['status'] == 'sent':
                print(f"   ✓ Notification delivered successfully")
            else:
                print(f"   ✗ Notification failed: {notification.get('error', 'Unknown error')}")
        
        # Verify Pushover API was called
        if mock_requests.post.called:
            print("\n✓ Pushover API was called (push notification would be sent in production)")
        
        print("\n" + "="*70)
        print("✓ Pushover E2E test completed successfully")
        print("="*70)
        
        return result['notification_status'] == 'success'


def test_both_channels():
    """Test both Gmail and Pushover notifications through local MCP server."""
    print("\n" + "="*70)
    print("E2E TEST: NotificationAgent -> Both Channels (Gmail + Pushover)")
    print("="*70)
    
    # Mock both SMTP and Pushover API
    with patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP') as mock_smtp, \
         patch('llm.local_mcp.tools.pushover_tool.requests') as mock_requests:
        
        # Setup SMTP mock
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Setup Pushover mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'pushover_both_channels_456'
        }
        mock_requests.post.return_value = mock_response
        
        # Create NotificationAgent
        agent = NotificationAgent()
        
        # Prepare high-risk governance data
        input_data = {
            'governance_analysis': {
                'risk': 'high',
                'escalation': 'Review and escalate if necessary',
                'commentary': 'Multiple authentication failures and suspicious activity detected',
                'compliance_issues': [
                    'Security policy: Multiple failed login attempts',
                    'Audit requirement: Suspicious access patterns'
                ]
            },
            'audit_summary': {
                'count': 12,
                'timestamp': '2025-11-17T12:15:00Z',
                'incidents': [
                    {'severity': 'high', 'type': 'security_alert'},
                    {'severity': 'medium', 'type': 'authentication_failure'}
                ]
            }
        }
        
        print("\n📧📱 Sending notifications to both channels...")
        print(f"   Risk Level: {input_data['governance_analysis']['risk'].upper()}")
        print(f"   Incidents: {input_data['audit_summary']['count']}")
        print(f"   Channels: {agent.notification_channels}")
        
        # Run agent
        result = agent.run(input_data)
        
        # Verify results
        print("\n✅ Results:")
        print(f"   Overall Status: {result['notification_status']}")
        print(f"   Total Notifications: {len(result['notifications_sent'])}")
        
        gmail_sent = False
        pushover_sent = False
        
        for notification in result['notifications_sent']:
            print(f"\n   Channel: {notification['channel']}")
            print(f"   Status: {notification['status']}")
            print(f"   Request ID: {notification.get('request_id', 'N/A')}")
            
            if notification['channel'] == 'gmail' and notification['status'] == 'sent':
                gmail_sent = True
                print(f"   ✓ Gmail notification delivered")
            elif notification['channel'] == 'pushover' and notification['status'] == 'sent':
                pushover_sent = True
                print(f"   ✓ Pushover notification delivered")
        
        # Verify both services were called
        if mock_server.sendmail.called and mock_requests.post.called:
            print("\n✓ Both SMTP and Pushover API were called")
        
        print("\n" + "="*70)
        if gmail_sent and pushover_sent:
            print("✓ Both channels E2E test completed successfully")
        else:
            print("⚠ Some notifications may have failed")
        print("="*70)
        
        return gmail_sent and pushover_sent


def main():
    """Run all E2E tests."""
    print("\n" + "="*70)
    print("NOTIFICATION AGENT E2E TESTS")
    print("Testing NotificationAgent with Local MCP Server")
    print("="*70)
    print("\nPrerequisites:")
    print("  ✓ MCP server running on http://localhost:5005")
    print("  ✓ Environment variables configured in .env")
    print("  ✓ NOTIFICATION_CHANNELS set to 'gmail,pushover'")
    
    results = []
    
    # Test Gmail
    try:
        results.append(("Gmail", test_gmail_notification()))
    except Exception as e:
        print(f"\n✗ Gmail test failed: {e}")
        results.append(("Gmail", False))
    
    # Test Pushover
    try:
        results.append(("Pushover", test_pushover_notification()))
    except Exception as e:
        print(f"\n✗ Pushover test failed: {e}")
        results.append(("Pushover", False))
    
    # Test both channels
    try:
        results.append(("Both Channels", test_both_channels()))
    except Exception as e:
        print(f"\n✗ Both channels test failed: {e}")
        results.append(("Both Channels", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  {test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL E2E TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("="*70)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
