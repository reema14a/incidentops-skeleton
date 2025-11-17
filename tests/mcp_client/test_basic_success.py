"""Unit tests for MCPClient.

Tests for the HTTP-only MCP client implementation.
Connector classes have been removed in favor of a simplified HTTP-only approach.
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from llm.mcp_client import (
    MCPClient,
    MCPError,
    MCPConnectionError,
    MCPToolError,
    MCPTimeoutError,
    MCPConfigurationError,
    MCPResponseError
)


class TestMCPExceptions:
    """Test suite for MCP exception classes."""
    
    def test_mcp_error_base(self):
        """Test base MCPError exception."""
        error = MCPError("Test error", "TEST_CODE", {"key": "value"})
        
        assert error.message == "Test error"
        assert error.error_code == "TEST_CODE"
        assert error.context["key"] == "value"
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPError"
        assert error_dict["error_code"] == "TEST_CODE"
        assert error_dict["message"] == "Test error"
        assert error_dict["context"]["key"] == "value"
        
        # Test string representation
        error_str = str(error)
        assert "[TEST_CODE]" in error_str
        assert "Test error" in error_str
    
    def test_mcp_connection_error(self):
        """Test MCPConnectionError with connection details."""
        error = MCPConnectionError(
            "Connection failed",
            error_code="MCP_CONNECTION_FAILED",
            endpoint="http://localhost:8080",
            retry_count=3
        )
        
        assert error.message == "Connection failed"
        assert error.error_code == "MCP_CONNECTION_FAILED"
        assert error.context["endpoint"] == "http://localhost:8080"
        assert error.context["retry_count"] == 3
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPConnectionError"
        assert error_dict["context"]["endpoint"] == "http://localhost:8080"
    
    def test_mcp_tool_error(self):
        """Test MCPToolError with tool-specific details."""
        server_error = {"code": "INVALID_PARAMS", "message": "Missing parameter"}
        error = MCPToolError(
            "Tool invocation failed",
            error_code="MCP_TOOL_ERROR",
            tool_name="gmail.send",
            request_id="req-123",
            server_error=server_error
        )
        
        assert error.message == "Tool invocation failed"
        assert error.error_code == "MCP_TOOL_ERROR"
        assert error.context["tool_name"] == "gmail.send"
        assert error.context["request_id"] == "req-123"
        assert error.context["server_error"]["code"] == "INVALID_PARAMS"
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPToolError"
        assert error_dict["context"]["tool_name"] == "gmail.send"
    
    def test_mcp_timeout_error(self):
        """Test MCPTimeoutError with timing details."""
        error = MCPTimeoutError(
            "Operation timed out",
            timeout_seconds=30.0,
            operation="connect"
        )
        
        assert error.message == "Operation timed out"
        assert error.error_code == "MCP_TIMEOUT_ERROR"
        assert error.context["timeout_seconds"] == 30.0
        assert error.context["operation"] == "connect"
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPTimeoutError"
        assert error_dict["context"]["timeout_seconds"] == 30.0
    
    def test_mcp_configuration_error(self):
        """Test MCPConfigurationError with config details."""
        error = MCPConfigurationError(
            "Configuration missing",
            config_key="endpoint",
            config_file="settings.yaml"
        )
        
        assert error.message == "Configuration missing"
        assert error.error_code == "MCP_CONFIGURATION_ERROR"
        assert error.context["config_key"] == "endpoint"
        assert error.context["config_file"] == "settings.yaml"
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPConfigurationError"
        assert error_dict["context"]["config_key"] == "endpoint"
    
    def test_mcp_response_error(self):
        """Test MCPResponseError with response details."""
        error = MCPResponseError(
            "Invalid response format",
            response_data="invalid json {{",
            expected_format="JSON"
        )
        
        assert error.message == "Invalid response format"
        assert error.error_code == "MCP_RESPONSE_ERROR"
        assert error.context["response_data"] == "invalid json {{"
        assert error.context["expected_format"] == "JSON"
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPResponseError"
        assert error_dict["context"]["expected_format"] == "JSON"
    
    def test_exception_inheritance(self):
        """Test that all MCP exceptions inherit from MCPError."""
        assert issubclass(MCPConnectionError, MCPError)
        assert issubclass(MCPToolError, MCPError)
        assert issubclass(MCPTimeoutError, MCPError)
        assert issubclass(MCPConfigurationError, MCPError)
        assert issubclass(MCPResponseError, MCPError)


class TestMCPClient:
    """Test suite for MCPClient HTTP-only implementation."""
    
    @patch('config.settings_loader.get_settings')
    def test_client_initialization_with_defaults(self, mock_get_settings):
        """Test MCPClient initialization with default settings."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        client = MCPClient()
        
        assert client.endpoint == "http://localhost:8080"
        assert client.timeout == 30
        assert client.retry_delay == 2
        assert client.max_retries == 3
    
    @patch('config.settings_loader.get_settings')
    def test_client_initialization_with_overrides(self, mock_get_settings):
        """Test MCPClient initialization with parameter overrides."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        client = MCPClient(
            endpoint="https://custom:9000",
            timeout=60,
            retry_delay=5,
            max_retries=5
        )
        
        assert client.endpoint == "https://custom:9000"
        assert client.timeout == 60
        assert client.retry_delay == 5
        assert client.max_retries == 5
    
    @patch('config.settings_loader.get_settings')
    def test_client_initialization_missing_endpoint(self, mock_get_settings):
        """Test MCPClient raises error when endpoint is missing."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = None
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPClient()
        
        assert "endpoint is required" in str(exc_info.value).lower()
        assert exc_info.value.context["config_key"] == "endpoint"
    
    @patch('config.settings_loader.get_settings')
    def test_client_initialization_invalid_endpoint_protocol(self, mock_get_settings):
        """Test MCPClient raises error for invalid endpoint protocol."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "ftp://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPClient()
        
        assert "must begin with http://" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_call_tool_success(self, mock_get_settings, mock_post):
        """Test successful tool invocation."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "result": {"status": "sent", "message_id": "msg-123"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        result = client.call_tool("gmail.send", {"to": "test@example.com", "subject": "Test"})
        
        assert result["success"] is True
        assert result["result"]["status"] == "sent"
        assert result["result"]["message_id"] == "msg-123"
        assert result["tool_name"] == "gmail.send"
        assert "request_id" in result
        assert "timestamp" in result
        
        # Verify request was made correctly
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == "http://localhost:8080"
        assert call_args[1]["json"]["method"] == "tools/call"
        assert call_args[1]["json"]["params"]["name"] == "gmail.send"
        assert call_args[1]["timeout"] == 30
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_call_tool_server_error(self, mock_get_settings, mock_post):
        """Test tool invocation with server error response."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "error": {
                    "code": "INVALID_PARAMS",
                    "message": "Missing required parameter: to",
                    "data": {"param": "to"}
                }
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPToolError) as exc_info:
            client.call_tool("gmail.send", {"subject": "Test"})
        
        assert "gmail.send" in str(exc_info.value)
        assert exc_info.value.context["tool_name"] == "gmail.send"
        assert exc_info.value.context["server_error"]["code"] == "INVALID_PARAMS"
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_call_tool_invalid_json_response(self, mock_get_settings, mock_post):
        """Test tool invocation with invalid JSON response."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "doc", 0)
        mock_response.text = "Invalid JSON {{"
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "parse json" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_call_tool_missing_result_and_error(self, mock_get_settings, mock_post):
        """Test tool invocation with response missing both result and error."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"]  # Use the actual request ID
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "result" in str(exc_info.value).lower() and "error" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_retry_on_timeout(self, mock_sleep, mock_get_settings, mock_post):
        """Test tool invocation retries on timeout."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 2
        mock_get_settings.return_value = mock_settings
        
        # Mock timeout then success
        from requests.exceptions import Timeout
        
        # Track call count to return different responses
        call_count = [0]
        
        def mock_post_side_effect(url, json=None, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                raise Timeout("Connection timeout")
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "result": {"status": "sent"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        result = client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert result["success"] is True
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once_with(2)
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_max_retries_exhausted(self, mock_sleep, mock_get_settings, mock_post):
        """Test tool invocation fails after max retries."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 2
        mock_get_settings.return_value = mock_settings
        
        # Mock continuous timeout
        from requests.exceptions import Timeout
        mock_post.side_effect = Timeout("Connection timeout")
        
        client = MCPClient()
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert mock_post.call_count == 3  # Initial + 2 retries
        assert mock_sleep.call_count == 2  # Sleep between retries
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_custom_retry_parameters(self, mock_sleep, mock_get_settings, mock_post):
        """Test tool invocation respects custom retry_delay and max_retries."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 1
        mock_settings.notification.mcp.max_retries = 1
        mock_get_settings.return_value = mock_settings
        
        # Mock continuous connection error
        from requests.exceptions import ConnectionError
        mock_post.side_effect = ConnectionError("Connection refused")
        
        # Create client with custom retry parameters
        client = MCPClient(retry_delay=5, max_retries=4)
        
        with pytest.raises(MCPConnectionError):
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        # Verify it used custom parameters: initial + 4 retries = 5 attempts
        assert mock_post.call_count == 5
        # Verify it slept 4 times (between each retry) with custom delay
        assert mock_sleep.call_count == 4
        # Verify each sleep call used the custom retry_delay
        for call in mock_sleep.call_args_list:
            assert call[0][0] == 5
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_retry_on_http_error(self, mock_sleep, mock_get_settings, mock_post):
        """Test tool invocation retries on HTTP error status codes."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 1
        mock_settings.notification.mcp.max_retries = 2
        mock_get_settings.return_value = mock_settings
        
        # Track call count to return different responses
        call_count = [0]
        
        def mock_post_side_effect(url, json=None, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call returns HTTP 503 error
                mock_error_response = Mock()
                mock_error_response.status_code = 503
                mock_error_response.text = "Service Unavailable"
                return mock_error_response
            # Second call succeeds
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "result": {"status": "sent"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        result = client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert result["success"] is True
        assert mock_post.call_count == 2  # First failed, second succeeded
        assert mock_sleep.call_count == 1  # Slept once before retry
        mock_sleep.assert_called_with(1)
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_no_retry_on_response_error(self, mock_sleep, mock_get_settings, mock_post):
        """Test tool invocation does not retry on response parsing errors."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock invalid JSON response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid", "doc", 0)
        mock_response.text = "Invalid JSON"
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError):
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        # Should not retry on response errors
        assert mock_post.call_count == 1
        assert mock_sleep.call_count == 0
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_call_tool_http_error(self, mock_get_settings, mock_post):
        """Test tool invocation with HTTP error status."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock HTTP 500 error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPConnectionError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "500" in str(exc_info.value)
    
    @patch('config.settings_loader.get_settings')
    def test_context_manager(self, mock_get_settings):
        """Test MCPClient as context manager."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        with MCPClient() as client:
            assert client.endpoint == "http://localhost:8080"
        
        # No exception should be raised
    
    @patch('config.settings_loader.get_settings')
    def test_disconnect(self, mock_get_settings):
        """Test disconnect method (no-op for HTTP)."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        client = MCPClient()
        client.disconnect()  # Should not raise any exception


class TestJSONRPCValidation:
    """Test suite for strict JSON-RPC 2.0 format validation."""
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_missing_jsonrpc_field(self, mock_get_settings, mock_post):
        """Test response validation fails when 'jsonrpc' field is missing."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock response without 'jsonrpc' field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "test-id",
            "result": {"status": "sent"}
        }
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "jsonrpc" in str(exc_info.value).lower()
        assert "must contain" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_invalid_jsonrpc_version(self, mock_get_settings, mock_post):
        """Test response validation fails when 'jsonrpc' version is not '2.0'."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock response with wrong version
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "1.0",
            "id": "test-id",
            "result": {"status": "sent"}
        }
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "version must be '2.0'" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_missing_id_field(self, mock_get_settings, mock_post):
        """Test response validation fails when 'id' field is missing."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock response without 'id' field
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"status": "sent"}
        }
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "'id'" in str(exc_info.value).lower()
        assert "must contain" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_id_mismatch(self, mock_get_settings, mock_post):
        """Test response validation fails when response 'id' doesn't match request."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Mock response with mismatched id
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "id": "wrong-id",
            "result": {"status": "sent"}
        }
        mock_post.return_value = mock_response
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "mismatch" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_both_result_and_error(self, mock_get_settings, mock_post):
        """Test response validation fails when both 'result' and 'error' are present."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "result": {"status": "sent"},
                "error": {"code": "ERROR", "message": "Error"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "both" in str(exc_info.value).lower()
        assert "result" in str(exc_info.value).lower()
        assert "error" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_error_not_object(self, mock_get_settings, mock_post):
        """Test response validation fails when 'error' is not an object."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "error": "Error message"
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "error" in str(exc_info.value).lower()
        assert "object" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_error_missing_code(self, mock_get_settings, mock_post):
        """Test response validation fails when error object is missing 'code' field."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "error": {"message": "Error occurred"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "code" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_error_missing_message(self, mock_get_settings, mock_post):
        """Test response validation fails when error object is missing 'message' field."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "error": {"code": "ERROR_CODE"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        with pytest.raises(MCPResponseError) as exc_info:
            client.call_tool("gmail.send", {"to": "test@example.com"})
        
        assert "message" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_valid_jsonrpc_success_response(self, mock_get_settings, mock_post):
        """Test valid JSON-RPC 2.0 success response passes validation."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "result": {"status": "sent", "message_id": "msg-123"}
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        result = client.call_tool("gmail.send", {"to": "test@example.com"})
        
        # Should succeed without raising exception
        assert result["success"] is True
        assert result["result"]["status"] == "sent"
    
    @patch('llm.mcp_client.requests.post')
    @patch('config.settings_loader.get_settings')
    def test_valid_jsonrpc_error_response(self, mock_get_settings, mock_post):
        """Test valid JSON-RPC 2.0 error response passes validation."""
        mock_settings = Mock()
        mock_settings.notification.mcp.endpoint = "http://localhost:8080"
        mock_settings.notification.mcp.timeout = 30
        mock_settings.notification.mcp.retry_delay = 2
        mock_settings.notification.mcp.max_retries = 3
        mock_get_settings.return_value = mock_settings
        
        # Capture the request ID from the call
        def mock_post_side_effect(url, json=None, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "jsonrpc": "2.0",
                "id": json["id"],  # Use the actual request ID
                "error": {
                    "code": "INVALID_PARAMS",
                    "message": "Missing required parameter",
                    "data": {"param": "to"}
                }
            }
            return mock_response
        
        mock_post.side_effect = mock_post_side_effect
        
        client = MCPClient()
        
        # Should raise MCPToolError (not MCPResponseError) because format is valid
        with pytest.raises(MCPToolError) as exc_info:
            client.call_tool("gmail.send", {"subject": "Test"})
        
        # Verify it's a tool error, not a response format error
        assert exc_info.value.context["server_error"]["code"] == "INVALID_PARAMS"
