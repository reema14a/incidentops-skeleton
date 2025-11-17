#!/usr/bin/env python3
"""Real Pushover notification test with actual API credentials.

This script sends a real Pushover notification through the local MCP server
using the actual Pushover API credentials from the .env file.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.notification_agent import NotificationAgent


def test_real_pushover_notification():
    """Test real Pushover notification through local MCP server."""
    print("\n" + "="*70)
    print("REAL PUSHOVER NOTIFICATION TEST")
    print("Testing with actual Pushover API credentials")
    print("="*70)
    
    # Create NotificationAgent (will use real credentials from .env)
    agent = NotificationAgent()
    
    print(f"\nConfigured channels: {agent.notification_channels}")
    
    # Prepare critical-risk governance data to trigger notification
    input_data = {
        'governance_analysis': {
            'risk': 'critical',
            'escalation': 'Immediate escalation required',
            'commentary': 'Test notification from IncidentOps MCP integration',
            'compliance_issues': [
                'This is a test notification',
                'Validating Pushover integration'
            ]
        },
        'audit_summary': {
            'count': 1,
            'timestamp': '2025-11-17T11:45:00Z',
            'incidents': [
                {'severity': 'critical', 'type': 'test_notification'}
            ]
        }
    }
    
    print("\n📱 Sending real Pushover notification...")
    print(f"   Risk Level: {input_data['governance_analysis']['risk'].upper()}")
    print(f"   Message: {input_data['governance_analysis']['commentary']}")
    
    # Run agent
    result = agent.run(input_data)
    
    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Overall Status: {result['notification_status']}")
    print(f"Notifications Sent: {len(result['notifications_sent'])}")
    
    for notification in result['notifications_sent']:
        print(f"\n  Channel: {notification['channel']}")
        print(f"  Status: {notification['status']}")
        
        if notification['status'] == 'sent':
            print(f"  ✓ Notification delivered successfully")
            print(f"  Subject: {notification.get('subject', 'N/A')}")
            print(f"  Priority: {notification.get('priority', 'N/A')}")
            print(f"  Request ID: {notification.get('request_id', 'N/A')}")
            
            if 'mcp_result' in notification:
                mcp_result = notification['mcp_result']
                print(f"  MCP Result: {mcp_result.get('message', 'N/A')}")
                if 'request_id' in mcp_result:
                    print(f"  Pushover Request ID: {mcp_result['request_id']}")
        else:
            print(f"  ✗ Notification failed")
            print(f"  Error: {notification.get('error', 'Unknown error')}")
    
    print("\n" + "="*70)
    
    # Check if Pushover was sent successfully
    pushover_notifications = [n for n in result['notifications_sent'] if n['channel'] == 'pushover']
    
    if pushover_notifications and pushover_notifications[0]['status'] == 'sent':
        print("✓ PUSHOVER NOTIFICATION SENT SUCCESSFULLY")
        print("  Check your Pushover app for the notification!")
        print("="*70)
        return True
    else:
        print("✗ PUSHOVER NOTIFICATION FAILED")
        if pushover_notifications:
            print(f"  Error: {pushover_notifications[0].get('error', 'Unknown')}")
        print("="*70)
        return False


if __name__ == "__main__":
    try:
        success = test_real_pushover_notification()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
