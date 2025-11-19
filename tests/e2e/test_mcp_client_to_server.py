#!/usr/bin/env python3
"""End-to-end tests for MCPClient → Local MCP Server communication.

These tests verify the full integration between MCPClient and the Local MCP Server
for both gmail.send and pushover.send tools. The server is started in a background
thread, and the client makes real HTTP requests to it.

External services (SMTP, Pushover API) are mocked to avoid real network calls.
"""

import unittest
import threading
import time
import pytest
from unittest.mock import patch, MagicMock, Mock
from llm.mcp_client import MCPClient, MCPToolError, MCPConnectionError
from llm.local_mcp.server import app


# Global patches for external services
gmail_smtp_patcher = None
pushover_requests_patcher = None
gmail_settings_patcher = None
pushover_settings_patcher = None


class TestMCPClientToServerGmail(unittest.TestCase):
    """E2E tests for MCPClient → Local MCP Server → gmail.send."""
    
    @classmethod
    def setUpClass(cls):
        """Start the MCP server in a background thread with mocked external services."""
        global gmail_smtp_patcher, gmail_settings_patcher
        
        # Patch SMTP at module level so server uses mocked version
        gmail_smtp_patcher = patch('llm.local_mcp.tools.gmail_tool.smtplib.SMTP')
        cls.mock_smtp_class = gmail_smtp_patcher.start()
        
        # Patch settings at module level
        gmail_settings_patcher = patch('llm.local_mcp.tools.gmail_tool.get_settings')
        cls.mock_get_settings = gmail_settings_patcher.start()
        
        # Start server
        cls.server_thread = threading.Thread(
            target=lambda: app.run(host='127.0.0.1', port=5005, debug=False, use_reloader=False),
            daemon=True
        )
        cls.server_thread.start()
        # Give server time to start
        time.sleep(2)
    
    @classmethod
    def tearDownClass(cls):
        """Stop patches."""
        global gmail_smtp_patcher, gmail_settings_patcher
        if gmail_smtp_patcher:
            gmail_smtp_patcher.stop()
        if gmail_settings_patcher:
            gmail_settings_patcher.stop()
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = MCPClient(endpoint='http://127.0.0.1:5005/send')
        
        # Reset mocks for each test
        self.mock_smtp_class.reset_mock()
        self.mock_get_settings.reset_mock()
    
    def test_gmail_send_success(self):
        """Test successful email sending through MCPClient → Server → Gmail tool."""
        print("\n" + "="*60)
        print("E2E TEST - MCPClient → Server → gmail.send (SUCCESS)")
        print("="*60)
        
        # Mock settings to return Gmail credentials
        mock_settings = Mock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@example.com',
            'GMAIL_PASSWORD': 'test_app_password'
        }.get(key)
        self.mock_get_settings.return_value = mock_settings
        
        # Mock SMTP server
        mock_smtp_instance = MagicMock()
        self.mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
        
        # Call gmail.send through MCPClient
        print("\nCalling gmail.send through MCPClient...")
        result = self.client.call_tool(
            'gmail.send',
            {
                'to': 'recipient@example.com',
                'subject': 'Test Email',
                'body': 'This is a test email body'
            }
        )
        
        # Verify response structure
        self.assertTrue(result['success'], "Request should succeed")
        self.assertIn('result', result, "Response should contain result")
        self.assertIn('request_id', result, "Response should contain request_id")
        self.assertIn('tool_name', result, "Response should contain tool_name")
        self.assertEqual(result['tool_name'], 'gmail.send')
        
        print(f"  ✓ Success: {result['success']}")
        print(f"  ✓ Request ID: {result['request_id']}")
        print(f"  ✓ Tool Name: {result['tool_name']}")
        
        # Verify result content
        result_data = result['result']
        self.assertIn('Email sent to', result_data['message'])
        self.assertEqual(result_data['recipient'], 'recipient@example.com')
        self.assertEqual(result_data['subject'], 'Test Email')

        print(f"  ✓ Message: {result_data['message']}")
        print(f"  ✓ Recipient: {result_data['recipient']}")
        
        # Verify SMTP was called correctly
        mock_smtp_instance.starttls.assert_called_once()
        mock_smtp_instance.login.assert_called_once_with('test@example.com', 'test_app_password')
        mock_smtp_instance.sendmail.assert_called_once()
        
        print("  ✓ SMTP server was called correctly")
        print("="*60)
    
    def test_gmail_send_missing_credentials(self):
        """Test gmail.send fails gracefully when credentials are missing."""
        print("\n" + "="*60)
        print("E2E TEST - MCPClient → Server → gmail.send (MISSING CREDENTIALS)")
        print("="*60)
        
        # Mock settings to return None for credentials
        mock_settings = Mock()
        mock_settings.get_secret.return_value = None
        self.mock_get_settings.return_value = mock_settings
        
        # Call gmail.send through MCPClient - should fail
        print("\nCalling gmail.send with missing credentials...")
        error = None
        try:
            result = self.client.call_tool(
                'gmail.send',
                {
                    'to': 'recipient@example.com',
                    'subject': 'Test Email',
                    'body': 'This is a test email body'
                }
            )
            self.fail("Should have raised an exception")
        except Exception as e:
            error = e
            # Server returns HTTP 400 with JSON-RPC error, client treats as connection error
            self.assertIn("credentials", str(error).lower())
            self.assertIsInstance(error, MCPConnectionError)

        
        print(f"  ✓ Error raised: {type(error).__name__}")
        print(f"  ✓ Error message contains 'credentials'")
        print("  ✓ Correctly failed with missing credentials")
        print("="*60)
    
    def test_gmail_send_missing_parameters(self):
        """Test gmail.send fails when required parameters are missing."""
        print("\n" + "="*60)
        print("E2E TEST - MCPClient → Server → gmail.send (MISSING PARAMETERS)")
        print("="*60)
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@example.com',
            'GMAIL_PASSWORD': 'test_app_password'
        }.get(key)
        self.mock_get_settings.return_value = mock_settings
        
        # Call gmail.send with missing 'body' parameter
        print("\nCalling gmail.send with missing 'body' parameter...")
        error = None
        try:
            result = self.client.call_tool(
                'gmail.send',
                {
                    'to': 'recipient@example.com',
                    'subject': 'Test Email'
                    # Missing 'body'
                }
            )
            self.fail("Should have raised an exception")
        except Exception as e:
            error = e
            self.assertIn("missing required argument: body", str(error).lower())
            self.assertIsInstance(error, MCPConnectionError)


        
        print(f"  ✓ Error raised: {type(error).__name__}")
        print(f"  ✓ Error message contains 'body'")
        print("  ✓ Correctly failed with missing parameter")
        print("="*60)
    
    def test_gmail_send_smtp_failure(self):
        """Test gmail.send handles SMTP failures gracefully."""
        print("\n" + "="*60)
        print("E2E TEST - MCPClient → Server → gmail.send (SMTP FAILURE)")
        print("="*60)
        
        # Mock settings
        mock_settings = Mock()
        mock_settings.get_secret.side_effect = lambda key: {
            'GMAIL_USER': 'test@example.com',
            'GMAIL_PASSWORD': 'test_app_password'
        }.get(key)
        self.mock_get_settings.return_value = mock_settings
        
        # Mock SMTP to raise authentication error
        mock_smtp_instance = MagicMock()
        mock_smtp_instance.login.side_effect = Exception("SMTP authentication failed")
        self.mock_smtp_class.return_value.__enter__.return_value = mock_smtp_instance
        
        # Call gmail.send - should fail
        print("\nCalling gmail.send with SMTP failure...")
        error = None
        try:
            result = self.client.call_tool(
                'gmail.send',
                {
                    'to': 'recipient@example.com',
                    'subject': 'Test Email',
                    'body': 'This is a test email body'
                }
            )
            self.fail("Should have raised an exception")
        except Exception as e:
            error = e
            self.assertIn("authentication", str(error).lower())
            self.assertIsInstance(error, MCPConnectionError)

        
        print(f"  ✓ Error raised: {type(error).__name__}")
        print(f"  ✓ Error message contains 'authentication'")
        print("  ✓ Correctly handled SMTP failure")
        print("="*60)

class TestMCPClientToServerPushover(unittest.TestCase):
    """E2E tests for MCPClient → Local MCP Server → pushover.send."""

    @classmethod
    def setUpClass(cls):
        """Start server + patch requests.post and settings."""
        global pushover_requests_patcher, pushover_settings_patcher

        # PATCH EXACT FUNCTION THAT SERVER CALLS
        pushover_requests_patcher = patch(
            'llm.local_mcp.tools.pushover_tool.requests.post'
        )
        cls.mock_requests_post = pushover_requests_patcher.start()

        # Patch settings
        pushover_settings_patcher = patch(
            'llm.local_mcp.tools.pushover_tool.get_settings'
        )
        cls.mock_get_settings = pushover_settings_patcher.start()

        # Start server once
        cls.server_thread = threading.Thread(
            target=lambda: app.run(
                host='127.0.0.1', port=5005,
                debug=False, use_reloader=False
            ),
            daemon=True
        )
        cls.server_thread.start()

        time.sleep(1)  # allow server to start

    @classmethod
    def tearDownClass(cls):
        if pushover_requests_patcher:
            pushover_requests_patcher.stop()
        if pushover_settings_patcher:
            pushover_settings_patcher.stop()

    def setUp(self):
        self.client = MCPClient(endpoint="http://127.0.0.1:5005/send")

        # reset mocks
        self.mock_requests_post.reset_mock()
        self.mock_get_settings.reset_mock()

    @pytest.mark.skip(reason="Temporarily disabling this test")
    def test_pushover_send_success(self):
        mock_settings = Mock()
        mock_settings.get_secret.return_value = "test_pushover_token"
        self.mock_get_settings.return_value = mock_settings

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,
            "request": "pushover-req-12345"
        }
        self.mock_requests_post.return_value = mock_response

        result = self.client.call_tool(
            "pushover.send",
            {
                "user": "user_key_12345",
                "message": "Test notification message",
                "title": "Test Alert",
                "priority": 1
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["tool_name"], "pushover.send")
        self.assertEqual(result["result"]["request_id"], "pushover-req-12345")

        # check API call
        self.mock_requests_post.assert_called_once()
        payload = self.mock_requests_post.call_args.kwargs["data"]
        self.assertEqual(payload["token"], "test_pushover_token")

    def test_pushover_send_missing_token(self):
        mock_settings = Mock()
        mock_settings.get_secret.return_value = None
        self.mock_get_settings.return_value = mock_settings

        with self.assertRaises(MCPConnectionError):
            self.client.call_tool(
                "pushover.send",
                {"user": "user_key_12345", "message": "Test message"}
            )

    @pytest.mark.skip(reason="Temporarily disabling this test")
    def test_pushover_send_missing_parameters(self):
        mock_settings = Mock()
        mock_settings.get_secret.return_value = "test_pushover_token"
        self.mock_get_settings.return_value = mock_settings

        with self.assertRaises(MCPConnectionError) as cm:
            self.client.call_tool("pushover.send", {"user": "user_key_12345"})

        self.assertIn("message", str(cm.exception).lower())

    def test_pushover_send_api_failure(self):
        mock_settings = Mock()
        mock_settings.get_secret.return_value = "test_pushover_token"
        self.mock_get_settings.return_value = mock_settings

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid user key"
        self.mock_requests_post.return_value = mock_response

        with self.assertRaises(MCPConnectionError):
            self.client.call_tool(
                "pushover.send",
                {"user": "invalid_user_key", "message": "Test"}
            )

    @pytest.mark.skip(reason="Temporarily disabling this test")
    def test_pushover_send_with_default_title(self):
        mock_settings = Mock()
        mock_settings.get_secret.return_value = "test_pushover_token"
        self.mock_get_settings.return_value = mock_settings

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "status": 1,
            "request": "pushover-req-67890"
        }
        self.mock_requests_post.return_value = mock_response

        result = self.client.call_tool(
            "pushover.send",
            {"user": "user_key_12345", "message": "Hello!"}
        )

        self.assertTrue(result["success"])

        payload = self.mock_requests_post.call_args.kwargs["data"]
        self.assertEqual(payload["title"], "IncidentOps Notification")


class TestMCPClientToServerErrors(unittest.TestCase):
    """E2E tests for error handling in MCPClient → Local MCP Server communication."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.client = MCPClient(endpoint='http://127.0.0.1:5005/send')
    
    def test_unknown_tool(self):
        """Test calling an unknown tool returns proper error."""
        print("\n" + "="*60)
        print("E2E TEST - MCPClient → Server (UNKNOWN TOOL)")
        print("="*60)
        
        print("\nCalling unknown tool 'slack.send'...")
        error = None
        try:
            result = self.client.call_tool(
                'slack.send',
                {
                    'channel': '#alerts',
                    'message': 'Test message'
                }
            )
            self.fail("Should have raised an exception")
        except Exception as e:
            error = e
            self.assertIn('slack.send', str(error))
            self.assertIn('unknown', str(error).lower())
            self.assertIsInstance(error, MCPConnectionError)

        
        print(f"  ✓ Error raised: {type(error).__name__}")
        print(f"  ✓ Error message contains 'slack.send' and 'unknown'")
        print("  ✓ Correctly rejected unknown tool")
        print("="*60)


if __name__ == "__main__":
    # Run all E2E tests
    print("\n" + "="*60)
    print("STARTING E2E TESTS: MCPClient → Local MCP Server")
    print("="*60)
    
    unittest.main(verbosity=2)
