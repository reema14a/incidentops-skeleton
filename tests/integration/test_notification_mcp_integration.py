#!/usr/bin/env python3
"""Integration test for NotificationAgent with local MCP server.

This test verifies that NotificationAgent can successfully call the local MCP server
for both gmail and pushover tools, testing the full HTTP JSON-RPC flow.
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from agents.notification_agent import NotificationAgent
from llm.mcp_client import MCPClient
from llm.local_mcp.server import app


# Global server thread to avoid starting multiple servers
_server_thread = None
_server_started = False


def start_mcp_server():
    """Start the MCP server once for all tests."""
    global _server_thread, _server_started
    
    if not _server_started:
        _server_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=5006, debug=False, use_reloader=False),
            daemon=True
        )
        _server_thread.start()
        time.sleep(1.5)  # Give server time to start
        _server_started = True


class TestNotificationAgentMCPIntegration:
    """Integration tests for NotificationAgent with local MCP server."""
    
    @pytest.fixture(scope="class", autouse=True)
    def mcp_server(self):
        """Start local MCP server once for all tests in this class."""
        start_mcp_server()
        yield "http://127.0.0.1:5006/send"
    
    @pytest.fixture(autouse=True)
    def reset_settings_singleton(self, monkeypatch):
        """Reset settings singleton and set default env vars before each test."""
        from config.settings_loader import reset_settings
        reset_settings()
        
        # Set default environment variables for MCP client
        monkeypatch.setenv('MCP_ENDPOINT', 'http://127.0.0.1:5006/send')
        monkeypatch.setenv('MCP_TIMEOUT', '10')
        monkeypatch.setenv('MCP_MAX_RETRIES', '1')
        monkeypatch.setenv('MCP_RETRY_DELAY', '1')
        
        yield
        reset_settings()
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    def test_notification_agent_gmail_via_mcp_server(
        self,
        mock_smtp: MagicMock,
        monkeypatch
    ) -> None:
        """Test NotificationAgent sending Gmail notification via local MCP server."""
        print("\n" + "="*60)
        print("INTEGRATION TEST - NotificationAgent -> MCP Server -> Gmail")
        print("="*60)
        
        # Set environment variables for this test
        # Note: Even single channel needs trailing comma to be parsed as list
        monkeypatch.setenv('NOTIFICATION_CHANNELS', 'gmail,')  # Only Gmail channel
        monkeypatch.setenv('GMAIL_USER', 'test@gmail.com')
        monkeypatch.setenv('GMAIL_PASSWORD', 'test_password')
        monkeypatch.setenv('GMAIL_RECIPIENT', 'recipient@example.com')
        
        # Reset settings to pick up new env vars
        from config.settings_loader import reset_settings
        reset_settings()
        
        # Mock SMTP server
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Create NotificationAgent (will use env vars)
        agent = NotificationAgent()
        
        # Prepare input data (high risk to trigger notification)
        input_data = {
            'governance_analysis': {
                'risk': 'high',
                'escalation': 'Immediate review required',
                'commentary': 'Critical issues detected',
                'compliance_issues': ['Policy violation detected']
            },
            'audit_summary': {
                'count': 5,
                'timestamp': '2025-11-17T10:00:00Z'
            }
        }
        
        # Run agent
        print("\nSending notification via MCP server...")
        result = agent.run(input_data)
        
        # Verify result structure
        assert 'notification_status' in result
        assert 'notifications_sent' in result
        print(f"  ✓ Notification status: {result['notification_status']}")
        
        # Verify notification was sent successfully
        assert result['notification_status'] == 'success'
        assert len(result['notifications_sent']) == 1
        
        notification = result['notifications_sent'][0]
        assert notification['channel'] == 'gmail'
        assert notification['status'] == 'sent'
        assert 'request_id' in notification
        assert 'mcp_result' in notification
        print(f"  ✓ Gmail notification sent successfully")
        print(f"  ✓ Request ID: {notification['request_id']}")
        
        # Verify SMTP was called
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with('test@gmail.com', 'test_password')
        mock_server.sendmail.assert_called_once()
        print(f"  ✓ SMTP server called correctly")
        
        print("\n" + "="*60)
        print("✓ Gmail integration test passed")
        print("="*60)
    
    @patch('llm.local_mcp.tools.pushover_tool.requests')
    def test_notification_agent_pushover_via_mcp_server(
        self,
        mock_pushover_requests: MagicMock,
        monkeypatch
    ) -> None:
        """Test NotificationAgent sending Pushover notification via local MCP server."""
        print("\n" + "="*60)
        print("INTEGRATION TEST - NotificationAgent -> MCP Server -> Pushover")
        print("="*60)
        
        # Set environment variables for this test
        # Note: Even single channel needs trailing comma to be parsed as list
        monkeypatch.setenv('NOTIFICATION_CHANNELS', 'pushover,')  # Only Pushover channel
        monkeypatch.setenv('PUSHOVER_API_TOKEN', 'test_api_token')
        monkeypatch.setenv('PUSHOVER_USER_KEY', 'user_key_123')
        
        # Reset settings to pick up new env vars
        from config.settings_loader import reset_settings
        reset_settings()
        
        # Mock Pushover API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'pushover_request_id_456'
        }
        mock_pushover_requests.post.return_value = mock_response
        
        # Create NotificationAgent (will use env vars)
        agent = NotificationAgent()
        
        # Prepare input data (critical risk to trigger notification)
        input_data = {
            'governance_analysis': {
                'risk': 'critical',
                'escalation': 'Immediate escalation required',
                'commentary': 'System failure detected',
                'compliance_issues': []
            },
            'audit_summary': {
                'count': 10,
                'timestamp': '2025-11-17T10:30:00Z'
            }
        }
        
        # Run agent
        print("\nSending notification via MCP server...")
        result = agent.run(input_data)
        
        # Verify result structure
        assert 'notification_status' in result
        assert 'notifications_sent' in result
        print(f"  ✓ Notification status: {result['notification_status']}")
        
        # Verify notification was sent successfully
        assert result['notification_status'] == 'success'
        assert len(result['notifications_sent']) == 1
        
        notification = result['notifications_sent'][0]
        assert notification['channel'] == 'pushover'
        assert notification['status'] == 'sent'
        assert 'request_id' in notification
        assert 'mcp_result' in notification
        assert notification['mcp_result']['request_id'] == 'pushover_request_id_456'
        print(f"  ✓ Pushover notification sent successfully")
        print(f"  ✓ Request ID: {notification['request_id']}")
        
        # Verify Pushover API was called
        mock_pushover_requests.post.assert_called_once()
        call_args = mock_pushover_requests.post.call_args
        assert call_args[1]['data']['token'] == 'test_api_token'
        assert call_args[1]['data']['user'] == 'user_key_123'
        print(f"  ✓ Pushover API called correctly")
        
        print("\n" + "="*60)
        print("✓ Pushover integration test passed")
        print("="*60)
    
    @patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
    @patch('llm.local_mcp.tools.pushover_tool.requests')
    def test_notification_agent_both_channels_via_mcp_server(
        self,
        mock_pushover_requests: MagicMock,
        mock_smtp: MagicMock,
        monkeypatch
    ) -> None:
        """Test NotificationAgent sending to both Gmail and Pushover via MCP server."""
        print("\n" + "="*60)
        print("INTEGRATION TEST - NotificationAgent -> MCP Server -> Both Channels")
        print("="*60)
        
        # Set environment variables for this test
        monkeypatch.setenv('NOTIFICATION_CHANNELS', 'gmail,pushover')  # Both channels
        monkeypatch.setenv('GMAIL_USER', 'test@gmail.com')
        monkeypatch.setenv('GMAIL_PASSWORD', 'test_password')
        monkeypatch.setenv('GMAIL_RECIPIENT', 'recipient@example.com')
        monkeypatch.setenv('PUSHOVER_API_TOKEN', 'test_api_token')
        monkeypatch.setenv('PUSHOVER_USER_KEY', 'user_key_123')
        
        # Reset settings to pick up new env vars
        from config.settings_loader import reset_settings
        reset_settings()
        
        # Mock SMTP server (called by MCP server tool)
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Mock Pushover API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': 1,
            'request': 'pushover_request_id_789'
        }
        mock_pushover_requests.post.return_value = mock_response
        
        # Create NotificationAgent (will use env vars)
        agent = NotificationAgent()
        
        # Prepare input data (high risk to trigger notification)
        input_data = {
            'governance_analysis': {
                'risk': 'high',
                'escalation': 'Review required',
                'commentary': 'Multiple issues detected',
                'compliance_issues': ['Issue 1', 'Issue 2']
            },
            'audit_summary': {
                'count': 7,
                'timestamp': '2025-11-17T11:00:00Z'
            }
        }
        
        # Run agent
        print("\nSending notifications to both channels via MCP server...")
        result = agent.run(input_data)
        
        # Verify result structure
        assert 'notification_status' in result
        assert 'notifications_sent' in result
        print(f"  ✓ Notification status: {result['notification_status']}")
        
        # Verify both notifications were sent successfully
        assert result['notification_status'] == 'success'
        assert len(result['notifications_sent']) == 2
        
        # Check Gmail notification
        gmail_notification = next(n for n in result['notifications_sent'] if n['channel'] == 'gmail')
        assert gmail_notification['status'] == 'sent'
        print(f"  ✓ Gmail notification sent")
        
        # Check Pushover notification
        pushover_notification = next(n for n in result['notifications_sent'] if n['channel'] == 'pushover')
        assert pushover_notification['status'] == 'sent'
        print(f"  ✓ Pushover notification sent")
        
        # Verify both services were called
        mock_server.sendmail.assert_called_once()
        mock_pushover_requests.post.assert_called_once()
        print(f"  ✓ Both services called correctly")
        
        print("\n" + "="*60)
        print("✓ Both channels integration test passed")
        print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
