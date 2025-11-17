"""Unit tests for Local MCP Server logging functionality.

Tests that logging meets the requirements:
- Logs to both console and file (logs/mcp_server.log)
- Includes required fields: timestamp, logger name, request_id, tool name, status
- Never logs secrets
- Logs tool arguments after redacting secrets
- Logs full exception traces on failures
"""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from llm.local_mcp.server import _redact_secrets


class TestSecretRedaction:
    """Test cases for secret redaction in logging."""
    
    def test_redact_password_field(self) -> None:
        """Test that password fields are redacted."""
        arguments = {
            "username": "test@example.com",
            "password": "secret123",
            "subject": "Test"
        }
        
        result = _redact_secrets(arguments)
        
        assert result["username"] == "test@example.com"
        assert result["password"] == "[REDACTED]"
        assert result["subject"] == "Test"
    
    def test_redact_token_field(self) -> None:
        """Test that token fields are redacted."""
        arguments = {
            "api_token": "abc123xyz",
            "message": "Hello"
        }
        
        result = _redact_secrets(arguments)
        
        assert result["api_token"] == "[REDACTED]"
        assert result["message"] == "Hello"
    
    def test_redact_user_key_field(self) -> None:
        """Test that user_key fields are redacted."""
        arguments = {
            "user_key": "userkey123",
            "title": "Notification"
        }
        
        result = _redact_secrets(arguments)
        
        assert result["user_key"] == "[REDACTED]"
        assert result["title"] == "Notification"
    
    def test_redact_multiple_secret_fields(self) -> None:
        """Test that multiple secret fields are redacted."""
        arguments = {
            "username": "user",
            "password": "pass123",
            "api_key": "key456",
            "message": "Test message"
        }
        
        result = _redact_secrets(arguments)
        
        assert result["username"] == "user"
        assert result["password"] == "[REDACTED]"
        assert result["api_key"] == "[REDACTED]"
        assert result["message"] == "Test message"
    
    def test_no_secrets_to_redact(self) -> None:
        """Test that non-secret fields are not redacted."""
        arguments = {
            "to": "test@example.com",
            "subject": "Test",
            "body": "Test body"
        }
        
        result = _redact_secrets(arguments)
        
        assert result == arguments
    
    def test_case_insensitive_redaction(self) -> None:
        """Test that redaction is case-insensitive."""
        arguments = {
            "Password": "secret",
            "API_KEY": "key123",
            "Token": "token456"
        }
        
        result = _redact_secrets(arguments)
        
        assert result["Password"] == "[REDACTED]"
        assert result["API_KEY"] == "[REDACTED]"
        assert result["Token"] == "[REDACTED]"
    
    def test_empty_arguments(self) -> None:
        """Test redaction with empty arguments."""
        arguments = {}
        
        result = _redact_secrets(arguments)
        
        assert result == {}


class TestLoggingFormat:
    """Test cases for logging format and structure."""
    
    @patch('llm.local_mcp.router.logger')
    def test_log_format_includes_request_id(self, mock_logger: MagicMock) -> None:
        """Test that log messages include request_id."""
        from llm.local_mcp.router import route_tool_call
        
        # Mock the tool to avoid actual execution
        with patch('llm.local_mcp.tools.gmail_tool.gmail_send') as mock_gmail:
            mock_gmail.return_value = {"success": True}
            
            route_tool_call('gmail.send', {"to": "test@example.com"}, request_id="test-123")
            
            # Verify logger was called with request_id in the message
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            assert any('request_id=test-123' in str(call) for call in debug_calls)
    
    @patch('llm.local_mcp.router.logger')
    def test_log_format_includes_tool_name(self, mock_logger: MagicMock) -> None:
        """Test that log messages include tool name."""
        from llm.local_mcp.router import route_tool_call
        
        # Mock the tool to avoid actual execution
        with patch('llm.local_mcp.tools.pushover_tool.pushover_send') as mock_pushover:
            mock_pushover.return_value = {"success": True}
            
            route_tool_call('pushover.send', {"user": "user123", "message": "test"}, request_id="test-456")
            
            # Verify logger was called with tool name in the message
            debug_calls = [str(call) for call in mock_logger.debug.call_args_list]
            assert any('pushover.send' in str(call) for call in debug_calls)
