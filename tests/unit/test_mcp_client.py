"""Unit tests for MCPClient.

Tests will be implemented for dual transport modes (WebSocket and viaSocket HTTP)
in subsequent tasks after the new architecture is implemented.
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
    MCPResponseError,
    MCPWebSocketConnector,
    MCPViaSocketHTTPConnector,
    MCPViaSocketSSEConnector,
    is_viasocket_endpoint,
    is_websocket_endpoint
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
            endpoint="ws://test-endpoint",
            retry_count=3
        )
        
        assert error.message == "Connection failed"
        assert error.error_code == "MCP_CONNECTION_FAILED"
        assert error.context["endpoint"] == "ws://test-endpoint"
        assert error.context["retry_count"] == 3
        
        # Test to_dict()
        error_dict = error.to_dict()
        assert error_dict["error_type"] == "MCPConnectionError"
        assert error_dict["context"]["endpoint"] == "ws://test-endpoint"
    
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


class TestMCPWebSocketConnector:
    """Test suite for MCPWebSocketConnector."""
    
    @patch('llm.mcp_client.websocket')
    def test_connector_initialization(self, mock_websocket):
        """Test WebSocket connector initialization."""
        connector = MCPWebSocketConnector(
            endpoint="ws://localhost:8080",
            timeout=30.0,
            retry_delay=2.0,
            max_retries=3
        )
        
        assert connector.endpoint == "ws://localhost:8080"
        assert connector.timeout == 30.0
        assert connector.retry_delay == 2.0
        assert connector.max_retries == 3
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.websocket')
    def test_open_connection_success(self, mock_websocket):
        """Test successful WebSocket connection."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        assert connector.is_connected()
        mock_websocket.create_connection.assert_called_once_with(
            "ws://localhost:8080",
            timeout=30.0
        )
    
    @patch('llm.mcp_client.websocket')
    def test_open_connection_already_connected(self, mock_websocket):
        """Test that open() is idempotent when already connected."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        connector.open()  # Second call should not create new connection
        
        assert connector.is_connected()
        assert mock_websocket.create_connection.call_count == 1
    
    @patch('llm.mcp_client.websocket')
    def test_open_connection_timeout(self, mock_websocket):
        """Test connection timeout handling."""
        # Create a proper exception class that can be caught
        class WebSocketTimeoutException(Exception):
            pass
        
        mock_websocket.WebSocketTimeoutException = WebSocketTimeoutException
        mock_websocket.create_connection.side_effect = WebSocketTimeoutException("Timeout")
        
        connector = MCPWebSocketConnector("ws://localhost:8080", timeout=5.0)
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            connector.open()
        
        assert exc_info.value.context["timeout_seconds"] == 5.0
        assert exc_info.value.context["operation"] == "connect"
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.websocket')
    def test_open_connection_failure(self, mock_websocket):
        """Test connection failure handling."""
        mock_websocket.create_connection.side_effect = Exception("Connection refused")
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.open()
        
        assert "connection refused" in str(exc_info.value).lower()
        assert exc_info.value.context["endpoint"] == "ws://localhost:8080"
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.websocket')
    def test_close_connection(self, mock_websocket):
        """Test closing WebSocket connection."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        assert connector.is_connected()
        
        connector.close()
        assert not connector.is_connected()
        mock_ws.close.assert_called_once()
    
    @patch('llm.mcp_client.websocket')
    def test_close_connection_idempotent(self, mock_websocket):
        """Test that close() is idempotent."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        connector.close()
        connector.close()  # Second close should not raise error
        
        assert not connector.is_connected()
        assert mock_ws.close.call_count == 1
    
    @patch('llm.mcp_client.websocket')
    def test_send_message_success(self, mock_websocket):
        """Test sending message via WebSocket."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        message = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        connector.send(message)
        
        # Verify message was JSON-encoded and sent
        sent_data = mock_ws.send.call_args[0][0]
        assert json.loads(sent_data) == message
    
    @patch('llm.mcp_client.websocket')
    def test_send_message_not_connected(self, mock_websocket):
        """Test that send() raises error when not connected."""
        connector = MCPWebSocketConnector("ws://localhost:8080")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.send({"test": "data"})
        
        assert "not connected" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.websocket')
    def test_send_message_timeout(self, mock_websocket):
        """Test send timeout handling."""
        # Create a proper exception class that can be caught
        class WebSocketTimeoutException(Exception):
            pass
        
        mock_websocket.WebSocketTimeoutException = WebSocketTimeoutException
        mock_ws = Mock()
        mock_ws.send.side_effect = WebSocketTimeoutException("Send timeout")
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080", timeout=10.0)
        connector.open()
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            connector.send({"test": "data"})
        
        assert exc_info.value.context["timeout_seconds"] == 10.0
        assert exc_info.value.context["operation"] == "send"
    
    @patch('llm.mcp_client.websocket')
    def test_receive_message_success(self, mock_websocket):
        """Test receiving message via WebSocket."""
        mock_ws = Mock()
        response_data = {"jsonrpc": "2.0", "result": "success", "id": "123"}
        mock_ws.recv.return_value = json.dumps(response_data)
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        response = connector.receive()
        
        assert response == response_data
        mock_ws.settimeout.assert_called_with(30.0)
    
    @patch('llm.mcp_client.websocket')
    def test_receive_message_custom_timeout(self, mock_websocket):
        """Test receiving message with custom timeout."""
        mock_ws = Mock()
        mock_ws.recv.return_value = json.dumps({"result": "ok"})
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        connector.receive(timeout=15.0)
        
        mock_ws.settimeout.assert_called_with(15.0)
    
    @patch('llm.mcp_client.websocket')
    def test_receive_message_not_connected(self, mock_websocket):
        """Test that receive() raises error when not connected."""
        connector = MCPWebSocketConnector("ws://localhost:8080")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.receive()
        
        assert "not connected" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.websocket')
    def test_receive_message_timeout(self, mock_websocket):
        """Test receive timeout handling."""
        # Create a proper exception class that can be caught
        class WebSocketTimeoutException(Exception):
            pass
        
        mock_websocket.WebSocketTimeoutException = WebSocketTimeoutException
        mock_ws = Mock()
        mock_ws.recv.side_effect = WebSocketTimeoutException("Receive timeout")
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080", timeout=20.0)
        connector.open()
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            connector.receive()
        
        assert exc_info.value.context["timeout_seconds"] == 20.0
        assert exc_info.value.context["operation"] == "receive"
    
    @patch('llm.mcp_client.websocket')
    def test_receive_message_invalid_json(self, mock_websocket):
        """Test handling of invalid JSON response."""
        mock_ws = Mock()
        mock_ws.recv.return_value = "invalid json {{"
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        with pytest.raises(MCPResponseError) as exc_info:
            connector.receive()
        
        assert "invalid json" in str(exc_info.value).lower()
        assert exc_info.value.context["expected_format"] == "JSON"
    
    @patch('llm.mcp_client.websocket')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_success(self, mock_sleep, mock_websocket):
        """Test successful reconnection."""
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        connector = MCPWebSocketConnector("ws://localhost:8080")
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        # Should have called create_connection twice (initial + reconnect)
        assert mock_websocket.create_connection.call_count == 2
    
    @patch('llm.mcp_client.websocket')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_with_retries(self, mock_sleep, mock_websocket):
        """Test reconnection with multiple retry attempts."""
        mock_ws = Mock()
        # Fail first 2 attempts, succeed on 3rd
        mock_websocket.create_connection.side_effect = [
            mock_ws,  # Initial connection
            Exception("Connection failed"),  # First retry
            Exception("Connection failed"),  # Second retry
            mock_ws  # Third retry succeeds
        ]
        
        connector = MCPWebSocketConnector("ws://localhost:8080", max_retries=3, retry_delay=1.0)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        assert mock_websocket.create_connection.call_count == 4
        assert mock_sleep.call_count == 2  # Slept between retries
    
    @patch('llm.mcp_client.websocket')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_all_retries_fail(self, mock_sleep, mock_websocket):
        """Test reconnection failure after all retries exhausted."""
        mock_ws = Mock()
        mock_websocket.create_connection.side_effect = [
            mock_ws,  # Initial connection
            Exception("Connection failed"),
            Exception("Connection failed"),
            Exception("Connection failed")
        ]
        
        connector = MCPWebSocketConnector("ws://localhost:8080", max_retries=3, retry_delay=0.1)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.reconnect()
        
        assert not connector.is_connected()
        assert exc_info.value.context["retry_count"] == 3
        assert "after 3 attempts" in str(exc_info.value).lower()


class TestMCPViaSocketHTTPConnector:
    """Test suite for MCPViaSocketHTTPConnector."""
    
    @patch('llm.mcp_client.requests')
    def test_connector_initialization(self, mock_requests):
        """Test viaSocket HTTP connector initialization."""
        connector = MCPViaSocketHTTPConnector(
            endpoint="https://api.viasocket.com/mcp",
            timeout=30.0,
            retry_delay=2.0,
            max_retries=3
        )
        
        assert connector.endpoint == "https://api.viasocket.com/mcp"
        assert connector.timeout == 30.0
        assert connector.retry_delay == 2.0
        assert connector.max_retries == 3
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    def test_connector_initialization_invalid_endpoint(self, mock_requests):
        """Test that initialization fails for non-viaSocket endpoints."""
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPViaSocketHTTPConnector("https://example.com/mcp")
        
        assert "viasocket.com" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "MCP_CONFIGURATION_ERROR"
    
    @patch('llm.mcp_client.requests')
    def test_open_session_success(self, mock_requests):
        """Test successful HTTP session initialization."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        assert connector.is_connected()
        mock_requests.Session.assert_called_once()
        assert mock_session.headers.update.called
    
    @patch('llm.mcp_client.requests')
    def test_open_session_already_connected(self, mock_requests):
        """Test that open() is idempotent when already connected."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        connector.open()  # Second call should not create new session
        
        assert connector.is_connected()
        assert mock_requests.Session.call_count == 1
    
    @patch('llm.mcp_client.requests')
    def test_open_session_failure(self, mock_requests):
        """Test session initialization failure handling."""
        mock_requests.Session.side_effect = Exception("Session creation failed")
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.open()
        
        assert "session creation failed" in str(exc_info.value).lower()
        assert exc_info.value.context["endpoint"] == "https://api.viasocket.com/mcp"
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    def test_close_session(self, mock_requests):
        """Test closing HTTP session."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        assert connector.is_connected()
        
        connector.close()
        assert not connector.is_connected()
        mock_session.close.assert_called_once()
    
    @patch('llm.mcp_client.requests')
    def test_close_session_idempotent(self, mock_requests):
        """Test that close() is idempotent."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        connector.close()
        connector.close()  # Second close should not raise error
        
        assert not connector.is_connected()
        assert mock_session.close.call_count == 1
    
    @patch('llm.mcp_client.requests')
    def test_send_message_success(self, mock_requests):
        """Test preparing message for sending via HTTP."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        message = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        connector.send(message)
        
        # Verify message was stored for next receive() call
        assert hasattr(connector, '_pending_message')
        assert connector._pending_message == message
    
    @patch('llm.mcp_client.requests')
    def test_send_message_not_connected(self, mock_requests):
        """Test that send() raises error when not connected."""
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.send({"test": "data"})
        
        assert "not connected" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_success(self, mock_requests):
        """Test receiving message via HTTP POST."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        response_data = {"jsonrpc": "2.0", "result": "success", "id": "123"}
        mock_response.json.return_value = response_data
        mock_response.text = json.dumps(response_data)
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        message = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        connector.send(message)
        response = connector.receive()
        
        assert response == response_data
        mock_session.post.assert_called_once_with(
            "https://api.viasocket.com/mcp",
            json=message,
            timeout=30.0
        )
        # Verify pending message was cleared
        assert not hasattr(connector, '_pending_message')
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_custom_timeout(self, mock_requests):
        """Test receiving message with custom timeout."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        response_data = {"result": "ok"}
        mock_response.json.return_value = response_data
        mock_response.text = json.dumps(response_data)
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        connector.send({"test": "data"})
        connector.receive(timeout=15.0)
        
        # Verify custom timeout was used
        call_kwargs = mock_session.post.call_args[1]
        assert call_kwargs['timeout'] == 15.0
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_not_connected(self, mock_requests):
        """Test that receive() raises error when not connected."""
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.receive()
        
        assert "not connected" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_no_pending_message(self, mock_requests):
        """Test that receive() raises error when no message was sent."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.receive()
        
        assert "no message to send" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_http_error(self, mock_requests):
        """Test handling of HTTP error responses."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        connector.send({"test": "data"})
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.receive()
        
        assert "500" in str(exc_info.value)
        assert exc_info.value.context["status_code"] == 500
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_timeout(self, mock_requests):
        """Test receive timeout handling."""
        # Create the exception class first
        TimeoutException = type('Timeout', (Exception,), {})
        mock_requests.exceptions.Timeout = TimeoutException
        
        mock_session = Mock()
        mock_session.post.side_effect = TimeoutException("Request timeout")
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp", timeout=20.0)
        connector.open()
        
        connector.send({"test": "data"})
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            connector.receive()
        
        assert exc_info.value.context["timeout_seconds"] == 20.0
        assert exc_info.value.context["operation"] == "http_request"
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_invalid_json(self, mock_requests):
        """Test handling of invalid JSON response."""
        mock_session = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = "invalid json {{"
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        connector.send({"test": "data"})
        
        with pytest.raises(MCPResponseError) as exc_info:
            connector.receive()
        
        assert "invalid json" in str(exc_info.value).lower()
        assert exc_info.value.context["expected_format"] == "JSON"
    
    @patch('llm.mcp_client.requests')
    def test_receive_message_request_exception(self, mock_requests):
        """Test handling of general request exceptions."""
        # Create the exception class first
        RequestExceptionClass = type('RequestException', (Exception,), {})
        mock_requests.exceptions.RequestException = RequestExceptionClass
        
        mock_session = Mock()
        mock_session.post.side_effect = RequestExceptionClass("Network error")
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        connector.send({"test": "data"})
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.receive()
        
        assert "network error" in str(exc_info.value).lower()
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_success(self, mock_sleep, mock_requests):
        """Test successful reconnection."""
        mock_session = Mock()
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp")
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        # Should have called Session twice (initial + reconnect)
        assert mock_requests.Session.call_count == 2
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_with_retries(self, mock_sleep, mock_requests):
        """Test reconnection with multiple retry attempts."""
        mock_session = Mock()
        # Fail first 2 attempts, succeed on 3rd
        mock_requests.Session.side_effect = [
            mock_session,  # Initial connection
            Exception("Session failed"),  # First retry
            Exception("Session failed"),  # Second retry
            mock_session  # Third retry succeeds
        ]
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp", max_retries=3, retry_delay=1.0)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        assert mock_requests.Session.call_count == 4
        assert mock_sleep.call_count == 2  # Slept between retries
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_all_retries_fail(self, mock_sleep, mock_requests):
        """Test reconnection failure after all retries exhausted."""
        mock_session = Mock()
        mock_requests.Session.side_effect = [
            mock_session,  # Initial connection
            Exception("Session failed"),
            Exception("Session failed"),
            Exception("Session failed")
        ]
        
        connector = MCPViaSocketHTTPConnector("https://api.viasocket.com/mcp", max_retries=3, retry_delay=0.1)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.reconnect()
        
        assert not connector.is_connected()
        assert exc_info.value.context["retry_count"] == 3
        assert "after 3 attempts" in str(exc_info.value).lower()


class TestMCPViaSocketSSEConnector:
    """Test suite for MCPViaSocketSSEConnector."""
    
    @patch('llm.mcp_client.requests')
    def test_connector_initialization(self, mock_requests):
        """Test SSE connector initialization."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        connector = MCPViaSocketSSEConnector(
            endpoint="https://api.viasocket.com/mcp/sse",
            timeout=30.0,
            retry_delay=2.0,
            max_retries=3
        )
        
        assert connector.endpoint == "https://api.viasocket.com/mcp/sse"
        assert connector.send_url == "https://api.viasocket.com/mcp/send"
        assert connector.timeout == 30.0
        assert connector.retry_delay == 2.0
        assert connector.max_retries == 3
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    def test_connector_initialization_invalid_endpoint_no_sse(self, mock_requests):
        """Test that initialization fails for endpoints not ending with /sse."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPViaSocketSSEConnector("https://api.viasocket.com/mcp")
        
        assert "/sse" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "MCP_CONFIGURATION_ERROR"
    
    @patch('llm.mcp_client.requests')
    def test_connector_initialization_invalid_endpoint_no_viasocket(self, mock_requests):
        """Test that initialization fails for non-viaSocket endpoints."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPViaSocketSSEConnector("https://example.com/sse")
        
        assert "viasocket.com" in str(exc_info.value).lower()
        assert exc_info.value.error_code == "MCP_CONFIGURATION_ERROR"
    
    @patch('llm.mcp_client.requests')
    def test_open_stream_success(self, mock_requests):
        """Test successful SSE stream opening."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        assert connector.is_connected()
        mock_session.get.assert_called_once_with(
            "https://api.viasocket.com/mcp/sse",
            stream=True,
            timeout=30.0
        )
    
    @patch('llm.mcp_client.requests')
    def test_open_stream_already_connected(self, mock_requests):
        """Test that open() is idempotent when already connected."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        connector.open()  # Second call should not create new stream
        
        assert connector.is_connected()
        assert mock_session.get.call_count == 1
    
    @patch('llm.mcp_client.requests')
    def test_open_stream_connection_failure(self, mock_requests):
        """Test stream opening failure handling."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_session.get.side_effect = Exception("Connection failed")
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.open()
        
        assert "connection failed" in str(exc_info.value).lower()
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    def test_open_stream_http_error(self, mock_requests):
        """Test handling of HTTP error when opening stream."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 500
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.open()
        
        assert "500" in str(exc_info.value)
        assert not connector.is_connected()
    
    @patch('llm.mcp_client.requests')
    def test_close_stream(self, mock_requests):
        """Test closing SSE stream."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        assert connector.is_connected()
        
        connector.close()
        assert not connector.is_connected()
        mock_stream.close.assert_called_once()
        mock_session.close.assert_called_once()
    
    @patch('llm.mcp_client.requests')
    def test_send_message_success(self, mock_requests):
        """Test sending message via SSE /send endpoint."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_response = Mock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_stream
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        message = {"jsonrpc": "2.0", "method": "test", "id": "123"}
        connector.send(message)
        
        # Verify message was sent to /send endpoint
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == "https://api.viasocket.com/mcp/send"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
    
    @patch('llm.mcp_client.requests')
    def test_send_message_not_connected(self, mock_requests):
        """Test that send() raises error when not connected."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.send({"test": "data"})
        
        assert "not connected" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.requests')
    def test_send_message_http_error(self, mock_requests):
        """Test handling of HTTP error when sending."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_session.get.return_value = mock_stream
        mock_session.post.return_value = mock_response
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.send({"test": "data"})
        
        assert "500" in str(exc_info.value)
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_receive_message_success(self, mock_sleep, mock_requests):
        """Test receiving message from SSE buffer."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        # Manually add a response to the buffer
        response_data = {"jsonrpc": "2.0", "result": "success", "id": "123"}
        connector._response_buffer.append(response_data)
        
        response = connector.receive(timeout=1.0)
        
        assert response == response_data
        assert len(connector._response_buffer) == 0
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_receive_message_timeout(self, mock_sleep, mock_requests):
        """Test receive timeout when no messages in buffer."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        with pytest.raises(MCPTimeoutError) as exc_info:
            connector.receive(timeout=0.1)
        
        assert exc_info.value.context["timeout_seconds"] == 0.1
        assert exc_info.value.context["operation"] == "receive"
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_success(self, mock_sleep, mock_requests):
        """Test successful reconnection."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse")
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        # Should have called get twice (initial + reconnect)
        assert mock_session.get.call_count == 2
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_with_retries(self, mock_sleep, mock_requests):
        """Test reconnection with multiple retry attempts."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream_success = Mock()
        mock_stream_success.status_code = 200
        mock_stream_success.iter_lines.return_value = iter([])
        
        # Fail first 2 attempts, succeed on 3rd
        mock_session.get.side_effect = [
            mock_stream_success,  # Initial connection
            Exception("Connection failed"),  # First retry
            Exception("Connection failed"),  # Second retry
            mock_stream_success  # Third retry succeeds
        ]
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse", max_retries=3, retry_delay=0.1)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        connector.reconnect()
        
        assert connector.is_connected()
        assert mock_session.get.call_count == 4
        assert mock_sleep.call_count == 2  # Slept between retries
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_reconnect_all_retries_fail(self, mock_sleep, mock_requests):
        """Test reconnection failure after all retries exhausted."""
        from llm.mcp_client import MCPViaSocketSSEConnector
        
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        
        mock_session.get.side_effect = [
            mock_stream,  # Initial connection
            Exception("Connection failed"),
            Exception("Connection failed"),
            Exception("Connection failed")
        ]
        mock_requests.Session.return_value = mock_session
        
        connector = MCPViaSocketSSEConnector("https://api.viasocket.com/mcp/sse", max_retries=3, retry_delay=0.1)
        connector.open()
        
        # Simulate disconnection
        connector._connected = False
        
        with pytest.raises(MCPConnectionError) as exc_info:
            connector.reconnect()
        
        assert not connector.is_connected()
        assert exc_info.value.context["retry_count"] == 3
        assert "after 3 attempts" in str(exc_info.value).lower()


class TestMCPClient:
    """Test suite for MCPClient.
    
    Full implementation tests will be added after dual transport architecture
    is implemented in subsequent tasks.
    """
    
    def test_mcp_client_websocket_initialization(self):
        """Test MCPClient initialization with WebSocket endpoint."""
        client = MCPClient("ws://localhost:8080")
        
        assert client.endpoint == "ws://localhost:8080"
        assert isinstance(client._connector, MCPWebSocketConnector)
    
    def test_mcp_client_viasocket_http_initialization(self):
        """Test MCPClient initialization with viaSocket HTTP endpoint."""
        client = MCPClient("https://api.viasocket.com/mcp")
        
        assert client.endpoint == "https://api.viasocket.com/mcp"
        assert isinstance(client._connector, MCPViaSocketHTTPConnector)
    
    def test_mcp_client_viasocket_sse_initialization(self):
        """Test MCPClient initialization with viaSocket SSE endpoint."""
        client = MCPClient("https://api.viasocket.com/mcp/sse")
        
        assert client.endpoint == "https://api.viasocket.com/mcp/sse"
        # SSE should be detected before HTTP
        assert isinstance(client._connector, MCPViaSocketSSEConnector)
    
    def test_mcp_client_invalid_endpoint(self):
        """Test MCPClient initialization with invalid endpoint."""
        with pytest.raises(MCPConfigurationError) as exc_info:
            MCPClient("http://example.com")
        
        assert "unsupported" in str(exc_info.value).lower()
    
    @patch('llm.mcp_client.websocket')
    def test_call_tool_success(self, mock_websocket):
        """Test successful tool invocation via MCPClient."""
        # Setup mock WebSocket
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        # Mock response
        response_data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success", "data": "test result"}
        }
        mock_ws.recv.return_value = json.dumps(response_data)
        
        # Create client and invoke tool
        client = MCPClient("ws://localhost:8080")
        result = client.call_tool("test_tool", {"param1": "value1"})
        
        # Verify result structure
        assert result["success"] is True
        assert result["result"] == {"status": "success", "data": "test result"}
        assert result["tool_name"] == "test_tool"
        assert "request_id" in result
        assert "timestamp" in result
        
        # Verify connection was established
        assert mock_websocket.create_connection.called
        
        # Verify message was sent
        assert mock_ws.send.called
        sent_message = json.loads(mock_ws.send.call_args[0][0])
        assert sent_message["method"] == "tools/call"
        assert sent_message["params"]["name"] == "test_tool"
        assert sent_message["params"]["arguments"] == {"param1": "value1"}
    
    @patch('llm.mcp_client.websocket')
    def test_call_tool_with_error_response(self, mock_websocket):
        """Test tool invocation with error response from server."""
        # Setup mock WebSocket
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        
        # Mock error response
        error_response = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "error": {
                "code": "TOOL_NOT_FOUND",
                "message": "Tool 'unknown_tool' not found"
            }
        }
        mock_ws.recv.return_value = json.dumps(error_response)
        
        # Create client and invoke tool
        client = MCPClient("ws://localhost:8080")
        result = client.call_tool("unknown_tool", {})
        
        # Verify error structure
        assert result["success"] is False
        assert result["error"]["code"] == "TOOL_NOT_FOUND"
        assert result["error"]["message"] == "Tool 'unknown_tool' not found"
        assert result["tool_name"] == "unknown_tool"
    
    @patch('llm.mcp_client.websocket')
    def test_call_tool_auto_connect(self, mock_websocket):
        """Test that call_tool automatically connects if not connected."""
        # Setup mock WebSocket
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        mock_ws.recv.return_value = json.dumps({"jsonrpc": "2.0", "id": "1", "result": "ok"})
        
        # Create client without connecting
        client = MCPClient("ws://localhost:8080")
        assert not client._is_open
        
        # Call tool should auto-connect
        result = client.call_tool("test_tool", {})
        
        # Verify connection was established
        assert client._is_open
        assert result["success"] is True
    
    @patch('llm.mcp_client.websocket')
    def test_call_tool_connection_fails(self, mock_websocket):
        """Test tool invocation when connection fails."""
        # Setup mock to fail connection
        mock_websocket.create_connection.side_effect = Exception("Connection failed")
        
        # Create client
        client = MCPClient("ws://localhost:8080")
        
        # Call tool should fail with connection error during auto-connect
        with pytest.raises(MCPConnectionError) as exc_info:
            client.call_tool("test_tool", {})
        
        assert "connection failed" in str(exc_info.value).lower()
        assert exc_info.value.context["endpoint"] == "ws://localhost:8080"
    
    @patch('llm.mcp_client.websocket')
    def test_context_manager(self, mock_websocket):
        """Test MCPClient as context manager."""
        # Setup mock WebSocket
        mock_ws = Mock()
        mock_websocket.create_connection.return_value = mock_ws
        mock_ws.recv.return_value = json.dumps({"jsonrpc": "2.0", "id": "1", "result": "ok"})
        
        # Use client as context manager
        with MCPClient("ws://localhost:8080") as client:
            result = client.call_tool("test_tool", {})
            assert result["success"] is True
        
        # Verify connection was closed
        assert mock_ws.close.called
    
    @patch('llm.mcp_client.requests')
    @patch('llm.mcp_client.time.sleep')
    def test_call_tool_via_sse_success(self, mock_sleep, mock_requests):
        """Test successful tool invocation via SSE transport."""
        # Setup mock SSE
        mock_session = Mock()
        mock_stream = Mock()
        mock_stream.status_code = 200
        mock_stream.iter_lines.return_value = iter([])
        mock_session.get.return_value = mock_stream
        
        # Mock send response
        mock_send_response = Mock()
        mock_send_response.status_code = 200
        mock_session.post.return_value = mock_send_response
        
        mock_requests.Session.return_value = mock_session
        
        # Create client
        client = MCPClient("https://api.viasocket.com/mcp/sse")
        
        # Open connection first
        client._connector.open()
        
        # Now add response to buffer to simulate SSE event
        response_data = {
            "jsonrpc": "2.0",
            "id": "test-id",
            "result": {"status": "success", "data": "test result"}
        }
        client._connector._response_buffer.append(response_data)
        client._is_open = True  # Mark as already open
        
        result = client.call_tool("test_tool", {"param1": "value1"})
        
        # Verify result structure
        assert result["success"] is True
        assert result["result"] == {"status": "success", "data": "test result"}
        assert result["tool_name"] == "test_tool"
        assert "request_id" in result
        assert "timestamp" in result
        
        # Verify connection was established
        assert mock_session.get.called
        
        # Verify message was sent to /send endpoint
        assert mock_session.post.called
        call_args = mock_session.post.call_args
        assert "send" in call_args[0][0]
