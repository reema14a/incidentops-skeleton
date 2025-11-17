"""MCP Client for connecting to MCP servers and invoking tools.

This module provides a simplified MCPClient class that supports three transport modes:
- viaSocket SSE MCP servers (endpoints ending with /sse)
- viaSocket HTTP MCP servers (.viasocket.com)
- WebSocket MCP servers (ws:// or wss://)
"""

import logging
import json
import time
import uuid
import threading
from typing import Any, Optional, Dict, List

try:
    import websocket
except ImportError:
    websocket = None

try:
    import requests
    from requests.exceptions import RequestException
except ImportError:
    requests = None
    RequestException = Exception


class MCPError(Exception):
    """Base exception for MCP-related errors.
    
    Attributes:
        message (str): Human-readable error message.
        error_code (str): Machine-readable error code.
        context (dict): Additional context about the error.
    """
    
    def __init__(self, message: str, error_code: str = "MCP_ERROR", context: Optional[dict] = None):
        """Initialize MCP error with structured information.
        
        Args:
            message (str): Human-readable error message.
            error_code (str): Machine-readable error code for programmatic handling.
            context (dict, optional): Additional context about the error.
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging or serialization.
        
        Returns:
            dict: Structured error information.
        """
        return {
            "error_type": self.__class__.__name__,
            "error_code": self.error_code,
            "message": self.message,
            "context": self.context
        }
    
    def __str__(self) -> str:
        """Return string representation of the error.
        
        Returns:
            str: Formatted error message with code.
        """
        return f"[{self.error_code}] {self.message}"


class MCPConnectionError(MCPError):
    """Exception raised when MCP connection fails.
    
    This exception is raised for connection-related issues such as:
    - Unable to establish initial connection
    - Connection timeout
    - Network errors
    - Missing endpoint configuration
    """
    
    def __init__(self, message: str, error_code: str = "MCP_CONNECTION_ERROR", 
                 endpoint: Optional[str] = None, retry_count: int = 0, context: Optional[dict] = None):
        """Initialize connection error with additional connection details.
        
        Args:
            message (str): Human-readable error message.
            error_code (str): Specific connection error code.
            endpoint (str, optional): The endpoint that failed to connect.
            retry_count (int): Number of retry attempts made.
            context (dict, optional): Additional context about the error.
        """
        context = context or {}
        context.update({
            "endpoint": endpoint,
            "retry_count": retry_count
        })
        super().__init__(message, error_code, context)


class MCPToolError(MCPError):
    """Exception raised when MCP tool invocation fails.
    
    This exception is raised for tool-related issues such as:
    - Tool not found
    - Invalid parameters
    - Tool execution failure
    - Response parsing errors
    """
    
    def __init__(self, message: str, error_code: str = "MCP_TOOL_ERROR",
                 tool_name: Optional[str] = None, request_id: Optional[str] = None,
                 server_error: Optional[dict] = None, context: Optional[dict] = None):
        """Initialize tool error with tool-specific details.
        
        Args:
            message (str): Human-readable error message.
            error_code (str): Specific tool error code.
            tool_name (str, optional): Name of the tool that failed.
            request_id (str, optional): Request ID for tracing.
            server_error (dict, optional): Error response from MCP server.
            context (dict, optional): Additional context about the error.
        """
        context = context or {}
        context.update({
            "tool_name": tool_name,
            "request_id": request_id,
            "server_error": server_error
        })
        super().__init__(message, error_code, context)


class MCPTimeoutError(MCPError):
    """Exception raised when MCP operation times out.
    
    This exception is raised when:
    - Connection attempt exceeds timeout
    - Tool invocation takes too long
    - Response not received within timeout period
    """
    
    def __init__(self, message: str, timeout_seconds: float, operation: str = "unknown",
                 context: Optional[dict] = None):
        """Initialize timeout error with timing details.
        
        Args:
            message (str): Human-readable error message.
            timeout_seconds (float): Timeout duration that was exceeded.
            operation (str): Operation that timed out.
            context (dict, optional): Additional context about the error.
        """
        context = context or {}
        context.update({
            "timeout_seconds": timeout_seconds,
            "operation": operation
        })
        super().__init__(message, "MCP_TIMEOUT_ERROR", context)


class MCPConfigurationError(MCPError):
    """Exception raised when MCP configuration is invalid or missing.
    
    This exception is raised for configuration issues such as:
    - Missing required configuration
    - Invalid configuration values
    - Configuration file not found
    """
    
    def __init__(self, message: str, config_key: Optional[str] = None,
                 config_file: Optional[str] = None, context: Optional[dict] = None):
        """Initialize configuration error with config details.
        
        Args:
            message (str): Human-readable error message.
            config_key (str, optional): Configuration key that is invalid/missing.
            config_file (str, optional): Configuration file path.
            context (dict, optional): Additional context about the error.
        """
        context = context or {}
        context.update({
            "config_key": config_key,
            "config_file": config_file
        })
        super().__init__(message, "MCP_CONFIGURATION_ERROR", context)


class MCPResponseError(MCPError):
    """Exception raised when MCP server response is invalid or malformed.
    
    This exception is raised for response-related issues such as:
    - Invalid JSON response
    - Missing required fields
    - Unexpected response format
    """
    
    def __init__(self, message: str, response_data: Optional[str] = None,
                 expected_format: Optional[str] = None, context: Optional[dict] = None):
        """Initialize response error with response details.
        
        Args:
            message (str): Human-readable error message.
            response_data (str, optional): Raw response data that failed to parse.
            expected_format (str, optional): Expected response format.
            context (dict, optional): Additional context about the error.
        """
        context = context or {}
        context.update({
            "response_data": response_data[:200] if response_data else None,  # Truncate for logging
            "expected_format": expected_format
        })
        super().__init__(message, "MCP_RESPONSE_ERROR", context)


class MCPWebSocketConnector:
    """WebSocket-based MCP transport connector.
    
    Handles connections to standard MCP servers using WebSocket protocol
    (ws:// or wss:// endpoints).
    
    Attributes:
        endpoint (str): The WebSocket endpoint URL.
        timeout (float): Connection and operation timeout in seconds.
        retry_delay (float): Delay between reconnection attempts in seconds.
        max_retries (int): Maximum number of reconnection attempts.
        logger (logging.Logger): Logger instance for this connector.
    """
    
    def __init__(
        self,
        endpoint: str,
        timeout: float = 30.0,
        retry_delay: float = 2.0,
        max_retries: int = 3
    ):
        """Initialize the WebSocket connector.
        
        Args:
            endpoint (str): The WebSocket endpoint URL (ws:// or wss://).
            timeout (float): Connection and operation timeout in seconds.
            retry_delay (float): Delay between reconnection attempts.
            max_retries (int): Maximum number of reconnection attempts.
            
        Raises:
            MCPConfigurationError: If websocket library is not installed.
        """
        if websocket is None:
            raise MCPConfigurationError(
                "websocket-client library is required for WebSocket transport. "
                "Install it with: pip install websocket-client",
                config_key="transport"
            )
        
        self.endpoint = endpoint
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.logger = logging.getLogger("IncidentOps")
        
        self._ws: Optional[websocket.WebSocket] = None
        self._connected = False
    
    def open(self) -> None:
        """Establish WebSocket connection to the MCP server.
        
        Raises:
            MCPConnectionError: If connection fails.
            MCPTimeoutError: If connection times out.
        """
        if self._connected and self._ws:
            self.logger.debug(f"Already connected to {self.endpoint}")
            return
        
        self.logger.info(f"Connecting to WebSocket MCP server at {self.endpoint}")
        
        try:
            self._ws = websocket.create_connection(
                self.endpoint,
                timeout=self.timeout
            )
            self._connected = True
            self.logger.info(f"Successfully connected to {self.endpoint}")
            
        except Exception as e:
            # Check if it's a timeout exception by class name
            if 'timeout' in type(e).__name__.lower():
                self.logger.error(f"Connection timeout to {self.endpoint}: {e}")
                raise MCPTimeoutError(
                    f"Connection to {self.endpoint} timed out after {self.timeout}s",
                    timeout_seconds=self.timeout,
                    operation="connect"
                )
            else:
                self.logger.error(f"Failed to connect to {self.endpoint}: {e}")
                raise MCPConnectionError(
                    f"Failed to connect to {self.endpoint}: {str(e)}",
                    endpoint=self.endpoint,
                    retry_count=0
                )
    
    def close(self) -> None:
        """Close the WebSocket connection.
        
        This method is idempotent and safe to call multiple times.
        """
        if self._ws:
            try:
                self._ws.close()
                self.logger.info(f"Closed connection to {self.endpoint}")
            except Exception as e:
                self.logger.warning(f"Error closing connection: {e}")
            finally:
                self._ws = None
                self._connected = False
        else:
            self.logger.debug("Connection already closed")
    
    def reconnect(self) -> None:
        """Reconnect to the MCP server with retry logic.
        
        Raises:
            MCPConnectionError: If all reconnection attempts fail.
            MCPTimeoutError: If reconnection times out.
        """
        self.logger.info(f"Attempting to reconnect to {self.endpoint}")
        self.close()
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Reconnection attempt {attempt + 1}/{self.max_retries}")
                self.open()
                self.logger.info(f"Reconnection successful on attempt {attempt + 1}")
                return
            except (MCPConnectionError, MCPTimeoutError) as e:
                last_error = e
                self.logger.warning(
                    f"Reconnection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # All retries exhausted
        self.logger.error(f"Failed to reconnect after {self.max_retries} attempts")
        raise MCPConnectionError(
            f"Failed to reconnect to {self.endpoint} after {self.max_retries} attempts",
            endpoint=self.endpoint,
            retry_count=self.max_retries,
            context={"last_error": str(last_error)}
        )
    
    def send(self, message: Dict[str, Any]) -> None:
        """Send a message to the MCP server via WebSocket.
        
        Args:
            message (dict): The message to send (will be JSON-encoded).
            
        Raises:
            MCPConnectionError: If not connected or send fails.
            MCPTimeoutError: If send operation times out.
        """
        if not self._connected or not self._ws:
            raise MCPConnectionError(
                "Not connected to MCP server. Call open() first.",
                endpoint=self.endpoint
            )
        
        try:
            message_json = json.dumps(message)
            self.logger.debug(f"Sending message: {message_json[:200]}")
            self._ws.send(message_json)
            self.logger.debug("Message sent successfully")
            
        except Exception as e:
            # Check if it's a timeout exception by class name
            if 'timeout' in type(e).__name__.lower():
                self.logger.error(f"Send timeout: {e}")
                raise MCPTimeoutError(
                    f"Send operation timed out after {self.timeout}s",
                    timeout_seconds=self.timeout,
                    operation="send"
                )
            else:
                self.logger.error(f"Failed to send message: {e}")
                self._connected = False
                raise MCPConnectionError(
                    f"Failed to send message: {str(e)}",
                    endpoint=self.endpoint
                )
    
    def receive(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Receive a message from the MCP server via WebSocket.
        
        Args:
            timeout (float, optional): Timeout in seconds. Uses connector timeout if not specified.
            
        Returns:
            dict: The received message (JSON-decoded).
            
        Raises:
            MCPConnectionError: If not connected or receive fails.
            MCPTimeoutError: If receive operation times out.
            MCPResponseError: If response cannot be parsed as JSON.
        """
        if not self._connected or not self._ws:
            raise MCPConnectionError(
                "Not connected to MCP server. Call open() first.",
                endpoint=self.endpoint
            )
        
        recv_timeout = timeout if timeout is not None else self.timeout
        
        try:
            # Set socket timeout for this operation
            self._ws.settimeout(recv_timeout)
            raw_response = self._ws.recv()
            self.logger.debug(f"Received message: {raw_response[:200]}")
            
            # Parse JSON response
            try:
                response = json.loads(raw_response)
                return response
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                raise MCPResponseError(
                    f"Invalid JSON response from server: {str(e)}",
                    response_data=raw_response,
                    expected_format="JSON"
                )
            
        except MCPResponseError:
            # Re-raise MCPResponseError without wrapping
            raise
        except Exception as e:
            # Check if it's a timeout exception by class name
            if 'timeout' in type(e).__name__.lower():
                self.logger.error(f"Receive timeout: {e}")
                raise MCPTimeoutError(
                    f"Receive operation timed out after {recv_timeout}s",
                    timeout_seconds=recv_timeout,
                    operation="receive"
                )
            else:
                self.logger.error(f"Failed to receive message: {e}")
                self._connected = False
                raise MCPConnectionError(
                    f"Failed to receive message: {str(e)}",
                    endpoint=self.endpoint
                )
    
    def is_connected(self) -> bool:
        """Check if the connector is currently connected.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connected and self._ws is not None


class MCPViaSocketHTTPConnector:
    """HTTP/S-based MCP transport connector for viaSocket servers.
    
    Handles connections to viaSocket MCP servers using HTTP/S protocol.
    The viaSocket backend handles WebSocket upgrade internally, so this
    connector uses HTTP/S endpoints directly without client-side WebSocket logic.
    
    Attributes:
        endpoint (str): The HTTP/S endpoint URL (must contain .viasocket.com).
        timeout (float): Connection and operation timeout in seconds.
        retry_delay (float): Delay between reconnection attempts in seconds.
        max_retries (int): Maximum number of reconnection attempts.
        logger (logging.Logger): Logger instance for this connector.
    """
    
    def __init__(
        self,
        endpoint: str,
        timeout: float = 30.0,
        retry_delay: float = 2.0,
        max_retries: int = 3
    ):
        """Initialize the viaSocket HTTP connector.
        
        Args:
            endpoint (str): The HTTP/S endpoint URL (must contain .viasocket.com).
            timeout (float): Connection and operation timeout in seconds.
            retry_delay (float): Delay between reconnection attempts.
            max_retries (int): Maximum number of reconnection attempts.
            
        Raises:
            MCPConfigurationError: If requests library is not installed or endpoint is invalid.
        """
        if requests is None:
            raise MCPConfigurationError(
                "requests library is required for viaSocket HTTP transport. "
                "Install it with: pip install requests",
                config_key="transport"
            )
        
        # Validate that endpoint contains .viasocket.com
        if '.viasocket.com' not in endpoint.lower():
            raise MCPConfigurationError(
                f"viaSocket HTTP connector requires endpoint containing '.viasocket.com'. Got: {endpoint}",
                config_key="endpoint",
                context={"endpoint": endpoint}
            )
        
        self.endpoint = endpoint
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.logger = logging.getLogger("IncidentOps")
        
        self._session: Optional[requests.Session] = None
        self._connected = False
    
    def open(self) -> None:
        """Establish HTTP session to the viaSocket MCP server.
        
        For HTTP transport, this creates a requests Session object
        that will be reused for all subsequent requests.
        
        Raises:
            MCPConnectionError: If session creation fails.
        """
        if self._connected and self._session:
            self.logger.debug(f"Already connected to {self.endpoint}")
            return
        
        self.logger.info(f"Initializing HTTP session for viaSocket MCP server at {self.endpoint}")
        
        try:
            self._session = requests.Session()
            self._session.headers.update({
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            })
            
            # Perform a lightweight health check or connection test
            # For now, we'll just mark as connected since HTTP is stateless
            self._connected = True
            self.logger.info(f"Successfully initialized session for {self.endpoint}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize session for {self.endpoint}: {e}")
            raise MCPConnectionError(
                f"Failed to initialize HTTP session for {self.endpoint}: {str(e)}",
                endpoint=self.endpoint,
                retry_count=0
            )
    
    def close(self) -> None:
        """Close the HTTP session.
        
        This method is idempotent and safe to call multiple times.
        """
        if self._session:
            try:
                self._session.close()
                self.logger.info(f"Closed session for {self.endpoint}")
            except Exception as e:
                self.logger.warning(f"Error closing session: {e}")
            finally:
                self._session = None
                self._connected = False
        else:
            self.logger.debug("Session already closed")
    
    def reconnect(self) -> None:
        """Reconnect to the viaSocket MCP server with retry logic.
        
        For HTTP transport, this recreates the session object.
        
        Raises:
            MCPConnectionError: If all reconnection attempts fail.
        """
        self.logger.info(f"Attempting to reconnect to {self.endpoint}")
        self.close()
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Reconnection attempt {attempt + 1}/{self.max_retries}")
                self.open()
                self.logger.info(f"Reconnection successful on attempt {attempt + 1}")
                return
            except MCPConnectionError as e:
                last_error = e
                self.logger.warning(
                    f"Reconnection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # All retries exhausted
        self.logger.error(f"Failed to reconnect after {self.max_retries} attempts")
        raise MCPConnectionError(
            f"Failed to reconnect to {self.endpoint} after {self.max_retries} attempts",
            endpoint=self.endpoint,
            retry_count=self.max_retries,
            context={"last_error": str(last_error)}
        )
    
    def send(self, message: Dict[str, Any]) -> None:
        """Send a message to the viaSocket MCP server via HTTP POST.
        
        Note: For HTTP transport, send() stores the message to be sent
        with the next receive() call, as HTTP is request-response based.
        
        Args:
            message (dict): The message to send (will be JSON-encoded).
            
        Raises:
            MCPConnectionError: If not connected.
        """
        if not self._connected or not self._session:
            raise MCPConnectionError(
                "Not connected to MCP server. Call open() first.",
                endpoint=self.endpoint
            )
        
        # Store the message for the next receive() call
        # HTTP is request-response, so we send and receive together
        self._pending_message = message
        self.logger.debug(f"Prepared message for sending: {json.dumps(message)[:200]}")
    
    def receive(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Send the pending message and receive response from viaSocket MCP server.
        
        For HTTP transport, this performs the actual HTTP POST request
        with the message prepared by send(), and returns the response.
        
        Args:
            timeout (float, optional): Timeout in seconds. Uses connector timeout if not specified.
            
        Returns:
            dict: The received message (JSON-decoded).
            
        Raises:
            MCPConnectionError: If not connected or request fails.
            MCPTimeoutError: If request times out.
            MCPResponseError: If response cannot be parsed as JSON.
        """
        if not self._connected or not self._session:
            raise MCPConnectionError(
                "Not connected to MCP server. Call open() first.",
                endpoint=self.endpoint
            )
        
        if not hasattr(self, '_pending_message'):
            raise MCPConnectionError(
                "No message to send. Call send() before receive().",
                endpoint=self.endpoint
            )
        
        request_timeout = timeout if timeout is not None else self.timeout
        message = self._pending_message
        
        try:
            message_json = json.dumps(message)
            self.logger.debug(f"Sending HTTP POST to {self.endpoint}: {message_json[:200]}")
            
            # Send HTTP POST request
            try:
                response = self._session.post(
                    self.endpoint,
                    json=message,
                    timeout=request_timeout
                )
            except Exception as e:
                # Check if it's a timeout exception by class name
                if 'timeout' in type(e).__name__.lower():
                    self.logger.error(f"HTTP request timeout: {e}")
                    raise MCPTimeoutError(
                        f"HTTP request timed out after {request_timeout}s",
                        timeout_seconds=request_timeout,
                        operation="http_request"
                    )
                # Check if it's a requests exception by class name
                elif 'request' in type(e).__name__.lower():
                    self.logger.error(f"HTTP request failed: {e}")
                    self._connected = False
                    raise MCPConnectionError(
                        f"HTTP request failed: {str(e)}",
                        endpoint=self.endpoint
                    )
                else:
                    # Re-raise unknown exceptions
                    raise
            
            # Check HTTP status
            if response.status_code != 200:
                response_text = str(response.text) if hasattr(response, 'text') else ''
                self.logger.error(
                    f"HTTP error {response.status_code}: {response_text[:200]}"
                )
                raise MCPConnectionError(
                    f"HTTP request failed with status {response.status_code}: {response_text[:200]}",
                    endpoint=self.endpoint,
                    context={"status_code": response.status_code}
                )
            
            response_text = str(response.text) if hasattr(response, 'text') else ''
            self.logger.debug(f"Received HTTP response: {response_text[:200]}")
            
            # Parse JSON response
            try:
                response_data = response.json()
                # Clear pending message after successful send/receive
                delattr(self, '_pending_message')
                return response_data
            except json.JSONDecodeError as e:
                self.logger.error(f"Failed to parse JSON response: {e}")
                raise MCPResponseError(
                    f"Invalid JSON response from server: {str(e)}",
                    response_data=response_text,
                    expected_format="JSON"
                )
        
        except MCPResponseError:
            # Re-raise MCPResponseError without wrapping
            raise
        except MCPConnectionError:
            # Re-raise MCPConnectionError without wrapping
            raise
        except MCPTimeoutError:
            # Re-raise MCPTimeoutError without wrapping
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during HTTP request: {e}")
            self._connected = False
            raise MCPConnectionError(
                f"Unexpected error during HTTP request: {str(e)}",
                endpoint=self.endpoint
            )
    
    def is_connected(self) -> bool:
        """Check if the connector is currently connected.
        
        For HTTP transport, this checks if the session is initialized.
        
        Returns:
            bool: True if connected, False otherwise.
        """
        return self._connected and self._session is not None

class MCPViaSocketSSEConnector:
    """
    SSE-based MCP transport connector for viaSocket MCP servers.

    viaSocket uses a single /sse endpoint that:
    - Accepts JSON-RPC messages using POST to /send
    - Returns responses via Server Sent Events (SSE)
    
    This connector:
    - Creates a persistent SSE stream reader thread
    - Buffers incoming responses
    - Exposes send() and receive() similar to WebSocket connector
    """

    def __init__(
        self,
        endpoint: str,
        timeout: float = 30.0,
        retry_delay: float = 2.0,
        max_retries: int = 3
    ):
        if requests is None:
            raise MCPConfigurationError(
                "requests library is required for SSE transport. "
                "Install it with: pip install requests",
                config_key="transport"
            )
        
        if not endpoint.lower().endswith("/sse"):
            raise MCPConfigurationError(
                f"SSE connector requires endpoint ending with /sse. Got: {endpoint}",
                config_key="endpoint",
                context={"endpoint": endpoint}
            )
        
        # Validate that endpoint contains .viasocket.com
        if '.viasocket.com' not in endpoint.lower():
            raise MCPConfigurationError(
                f"SSE connector requires endpoint containing '.viasocket.com'. Got: {endpoint}",
                config_key="endpoint",
                context={"endpoint": endpoint}
            )

        self.endpoint = endpoint.rstrip("/")
        self.logger = logging.getLogger("IncidentOps")
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries

        # viaSocket defines a separate POST endpoint for sending
        # # Replace /sse with /send
        # self.send_url = self.endpoint.replace("/sse", "/send")
        # Strip /sse — get base project endpoint
        self.send_url = self.endpoint.rsplit("/", 1)[0]


        self._session = requests.Session()
        self._session.headers.update({
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        })

        # background SSE event buffer
        self._response_buffer: List[Dict[str, Any]] = []
        self._buffer_lock = threading.Lock()

        # reading thread
        self._stream_thread: Optional[threading.Thread] = None
        self._stop_stream = False
        self._connected = False

    # ----------------------------------------------------------------------
    # Open SSE stream
    # ----------------------------------------------------------------------
    def open(self) -> None:
        """Start the background SSE stream reader."""
        if self._connected:
            return

        self._stop_stream = False
        self._response_buffer.clear()

        self.logger.info(f"Opening SSE stream: {self.endpoint}")

        try:
            self._stream = self._session.get(
                self.endpoint,
                stream=True,
                timeout=self.timeout,
            )

            
        except Exception as e:
            self.logger.error(f"[SSEConnector.open] stream status_code={getattr(self._stream, 'status_code', None)} headers={getattr(self._stream, 'headers', {})}")

            raise MCPConnectionError(
                f"Failed to open SSE stream: {e}",
                endpoint=self.endpoint
            )

        self.logger.debug(f"[SSEConnector.open] stream status_code={getattr(self._stream, 'status_code', None)} headers={getattr(self._stream, 'headers', {})}")

        if self._stream.status_code != 200:
            raise MCPConnectionError(
                f"SSE stream connection returned status {self._stream.status_code}",
                endpoint=self.endpoint,
                context={"status_code": self._stream.status_code}
            )

        # Launch reader thread
        self._stream_thread = threading.Thread(
            target=self._read_stream,
            daemon=True
        )
        self._stream_thread.start()

        self._connected = True
        self.logger.info("SSE transport connected.")

    # ----------------------------------------------------------------------
    # Close stream + thread
    # ----------------------------------------------------------------------
    def close(self) -> None:
        self._stop_stream = True
        self._connected = False

        try:
            if hasattr(self, "_stream") and self._stream:
                self._stream.close()
        except Exception:
            pass

        try:
            self._session.close()
        except Exception:
            pass

        self.logger.info("SSE transport closed.")
    
    # ----------------------------------------------------------------------
    # Reconnect with retry logic
    # ----------------------------------------------------------------------
    def reconnect(self) -> None:
        """Reconnect to the SSE MCP server with retry logic.
        
        Raises:
            MCPConnectionError: If all reconnection attempts fail.
        """
        self.logger.info(f"Attempting to reconnect to {self.endpoint}")
        self.close()
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                self.logger.debug(f"Reconnection attempt {attempt + 1}/{self.max_retries}")
                self.open()
                self.logger.info(f"Reconnection successful on attempt {attempt + 1}")
                return
            except MCPConnectionError as e:
                last_error = e
                self.logger.warning(
                    f"Reconnection attempt {attempt + 1}/{self.max_retries} failed: {e}"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
        
        # All retries exhausted
        self.logger.error(f"Failed to reconnect after {self.max_retries} attempts")
        raise MCPConnectionError(
            f"Failed to reconnect to {self.endpoint} after {self.max_retries} attempts",
            endpoint=self.endpoint,
            retry_count=self.max_retries,
            context={"last_error": str(last_error)}
        )

    # ----------------------------------------------------------------------
    # SSE Reader Thread
    # ----------------------------------------------------------------------
    def _read_stream(self) -> None:
        """Background thread that consumes SSE stream and buffers responses."""
        self.logger.info("Starting SSE reader thread...")

        try:
            for raw_line in self._stream.iter_lines():
                if self._stop_stream:
                    break
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8").strip()

                # SSE sends lines like:
                # event: message
                # data: {...}

                if line.startswith("data:"):
                    try:
                        json_payload = line.replace("data:", "", 1).strip()
                        parsed = json.loads(json_payload)

                        with self._buffer_lock:
                            self._response_buffer.append(parsed)

                    except Exception as e:
                        self.logger.error(f"Invalid SSE JSON: {e}")

        except RequestException as e:
            self.logger.error(f"SSE connection error: {e}")
        except Exception as e:
            self.logger.error(f"SSE reader exception: {e}")

    # ----------------------------------------------------------------------
    # Send JSON-RPC over /send endpoint
    # ----------------------------------------------------------------------
    def send(self, message: Dict[str, Any]) -> None:
        """Send a JSON-RPC message via HTTP POST to /send."""
        if not self._connected:
            raise MCPConnectionError(
                "SSE connector not connected. Call open().",
                endpoint=self.endpoint
            )

        try:
            payload = json.dumps(message)
            self.logger.debug(f"SSE send → {payload[:200]}")

            # DEBUG logs:
            self.logger.debug(f"[SSEConnector.send] POSTing to send_url={self.send_url} payload={payload[:1000]}")
        
            resp = self._session.post(
                self.send_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            # DEBUG logs:
            self.logger.debug(f"[SSEConnector.send] POSTing to send_url={self.send_url} payload={payload[:1000]}")
        
            if resp.status_code != 200:
                txt = getattr(resp, "text", "<no-text>")
            
                self.logger.error(f"[SSEConnector.send] ERROR response.text (truncated 500): {txt[:500]}")
            
                raise MCPConnectionError(
                    f"SSE send returned error {resp.status_code}: {resp.text[:200]}",
                    endpoint=self.send_url
                )

        except RequestException as e:
            raise MCPConnectionError(
                f"Failed to POST to SSE send endpoint: {e}",
                endpoint=self.send_url
            )

    # ----------------------------------------------------------------------
    # Blocking receive() from SSE buffer
    # ----------------------------------------------------------------------
    def receive(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        Blocking receive: waits for an SSE JSON event that includes result/error.
        """
        if timeout is None:
            timeout = self.timeout

        start = time.time()

        while time.time() - start < timeout:
            with self._buffer_lock:
                if self._response_buffer:
                    return self._response_buffer.pop(0)

            time.sleep(0.05)

        # Timed out
        raise MCPTimeoutError(
            f"SSE receive() timed out after {timeout}s",
            timeout_seconds=timeout,
            operation="receive"
        )

    def is_connected(self) -> bool:
        return self._connected

def is_viasocket_endpoint(endpoint: str) -> bool:
    """Check if endpoint is a viaSocket HTTP endpoint.
    
    Args:
        endpoint (str): The MCP server endpoint URL.
        
    Returns:
        bool: True if viaSocket endpoint, False otherwise.
    """
    return '.viasocket.com' in endpoint.lower()


def is_websocket_endpoint(endpoint: str) -> bool:
    """Check if endpoint is a WebSocket endpoint.
    
    Args:
        endpoint (str): The MCP server endpoint URL.
        
    Returns:
        bool: True if WebSocket endpoint, False otherwise.
    """
    endpoint_lower = endpoint.lower().strip()
    return endpoint_lower.startswith('ws://') or endpoint_lower.startswith('wss://')


class MCPClient:
    """Simplified MCP client supporting two transport modes.
    
    Automatically routes to:
    - viaSocket HTTP transport if endpoint contains .viasocket.com
    - WebSocket transport if endpoint starts with ws:// or wss://
    
    Configuration loaded from SettingsLoader with dot-notation access.
    """
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        timeout: Optional[float] = None,
        retry_delay: Optional[float] = None,
        max_retries: Optional[int] = None
    ):
        """Initialize MCP client.
        
        Args:
            endpoint (str, optional): MCP server endpoint URL.
            timeout (float, optional): Connection timeout in seconds.
            retry_delay (float, optional): Delay between retries in seconds.
            max_retries (int, optional): Maximum number of retry attempts.
            
        Raises:
            MCPConfigurationError: If endpoint is not provided or invalid.
        """
        from config.settings_loader import get_settings
        
        self.logger = logging.getLogger("IncidentOps")
        settings = get_settings()
        
        # Resolve configuration with dot-notation access
        self.endpoint = endpoint if endpoint is not None else settings.notification.mcp.endpoint
        if not self.endpoint:
            raise MCPConfigurationError(
                "MCP endpoint is required. Set MCP_ENDPOINT environment variable or configure in settings.yaml",
                config_key="endpoint"
            )
        
        self.timeout = float(timeout if timeout is not None else settings.notification.mcp.timeout)
        self.retry_delay = float(retry_delay if retry_delay is not None else settings.notification.mcp.retry_delay)
        self.max_retries = int(max_retries if max_retries is not None else settings.notification.mcp.max_retries)
        
        # Detect transport and create connector
        # Priority: SSE > viaSocket HTTP > WebSocket
        if self.endpoint.lower().endswith("/sse"):
            self.logger.info("Using viaSocket SSE transport")
            self._connector = MCPViaSocketSSEConnector(
                endpoint=self.endpoint,
                timeout=self.timeout,
                retry_delay=self.retry_delay,
                max_retries=self.max_retries
            )
        elif is_viasocket_endpoint(self.endpoint):
            self.logger.info("Using viaSocket HTTP transport")
            self._connector = MCPViaSocketHTTPConnector(
                endpoint=self.endpoint,
                timeout=self.timeout,
                retry_delay=self.retry_delay,
                max_retries=self.max_retries
            )
        elif is_websocket_endpoint(self.endpoint):
            self.logger.info("Using WebSocket transport")
            self._connector = MCPWebSocketConnector(
                endpoint=self.endpoint,
                timeout=self.timeout,
                retry_delay=self.retry_delay,
                max_retries=self.max_retries
            )
        else:
            raise MCPConfigurationError(
                f"Unsupported endpoint format. Expected ws://, wss://, .viasocket.com, or /sse endpoint. Got: {self.endpoint}",
                config_key="endpoint"
            )
        
        # --- add this after the transport selection block in __init__ ---
        try:
            connector_type = type(self._connector).__name__
        except Exception:
            connector_type = str(self._connector)

        self.logger.error(f"[MCPClient.__init__] FINAL CONNECTOR TYPE: {connector_type}")
        # If SSE connector, log the send_url property (if available)
        if hasattr(self._connector, "send_url"):
            try:
                self.logger.error(f"[MCPClient.__init__] connector.send_url: {getattr(self._connector, 'send_url')}")
            except Exception as e:
                self.logger.error(f"[MCPClient.__init__] failed reading send_url: {e}")


        self._is_open = False
    
    def call_tool(self, tool_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Invoke an MCP tool.
        
        Args:
            tool_name (str): Name of the tool to invoke.
            params (dict, optional): Parameters for the tool invocation.
            
        Returns:
            dict: Normalized response with structure:
                {
                    "success": bool,
                    "result": Any (if success=True),
                    "error": dict (if success=False),
                    "request_id": str,
                    "tool_name": str,
                    "timestamp": str
                }
            
        Raises:
            MCPConnectionError: If connection fails.
            MCPToolError: If tool invocation fails.
            MCPTimeoutError: If operation times out.
        """
        if params is None:
            params = {}
        
        # inside call_tool(), before calling the transport-specific wrapper
        self.logger.error(f"[MCPClient.call_tool] Using connector: {type(self._connector).__name__}")
        # log connector attributes helpful for diagnosis
        for attr in ("endpoint", "send_url", "timeout"):
            if hasattr(self._connector, attr):
                try:
                    self.logger.error(f"[MCPClient.call_tool] connector.{attr} = {getattr(self._connector, attr)}")
                except Exception as e:
                    self.logger.error(f"[MCPClient.call_tool] failed to read connector.{attr}: {e}")

        # Auto-connect if needed
        if not self._is_open:
            self._connector.open()
            self._is_open = True
        


        # Route based on connector TYPE, not endpoint text
        if isinstance(self._connector, MCPViaSocketSSEConnector):
            return self._call_viasocket_sse_tool(tool_name, params)

        elif isinstance(self._connector, MCPViaSocketHTTPConnector):
            return self._call_viasocket_http_tool(tool_name, params)

        elif isinstance(self._connector, MCPWebSocketConnector):
            return self._call_websocket_tool(tool_name, params)

        else:
            raise MCPConfigurationError("Unknown connector type")
    
    def _call_viasocket_sse_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via viaSocket SSE transport.
        
        Args:
            tool_name (str): Tool name.
            params (dict): Tool parameters.
            
        Returns:
            dict: Normalized response.
        """
        request_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        transport_type = "SSE" 
        self.logger.info(f"Calling tool '{tool_name}' via {transport_type} (request_id={request_id})")
        
        try:
            self.logger.error(f"[MCPClient._call_viasocket_sse_tool] sending request id={request_id} via connector {type(self._connector).__name__}")

            self._connector.send(request)
            response = self._connector.receive(timeout=self.timeout)
            return self._normalize_response(response, request_id, tool_name, timestamp)
        except (MCPConnectionError, MCPTimeoutError, MCPResponseError) as e:
            self._is_open = False
            self.logger.error(f"Tool invocation failed: {e}")
            raise MCPToolError(
                f"Tool '{tool_name}' invocation failed: {str(e)}",
                tool_name=tool_name,
                request_id=request_id
            )

    def _call_viasocket_http_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via viaSocket HTTP transport.
        
        Args:
            tool_name (str): Tool name.
            params (dict): Tool parameters.
            
        Returns:
            dict: Normalized response.
        """
        request_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        transport_type = "SSE" if self.endpoint.lower().endswith("/sse") else "HTTP"
        self.logger.info(f"Calling tool '{tool_name}' via {transport_type} (request_id={request_id})")
        
        try:
            self._connector.send(request)
            response = self._connector.receive(timeout=self.timeout)
            return self._normalize_response(response, request_id, tool_name, timestamp)
        except (MCPConnectionError, MCPTimeoutError, MCPResponseError) as e:
            self._is_open = False
            self.logger.error(f"Tool invocation failed: {e}")
            raise MCPToolError(
                f"Tool '{tool_name}' invocation failed: {str(e)}",
                tool_name=tool_name,
                request_id=request_id
            )
    
    def _call_websocket_tool(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Call tool via WebSocket transport.
        
        Args:
            tool_name (str): Tool name.
            params (dict): Tool parameters.
            
        Returns:
            dict: Normalized response.
        """
        request_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params
            }
        }
        
        self.logger.info(f"Calling tool '{tool_name}' via WebSocket (request_id={request_id})")
        
        try:
            self._connector.send(request)
            response = self._connector.receive(timeout=self.timeout)
            return self._normalize_response(response, request_id, tool_name, timestamp)
        except (MCPConnectionError, MCPTimeoutError, MCPResponseError) as e:
            self._is_open = False
            self.logger.error(f"Tool invocation failed: {e}")
            raise MCPToolError(
                f"Tool '{tool_name}' invocation failed: {str(e)}",
                tool_name=tool_name,
                request_id=request_id
            )
    
    def _normalize_response(
        self,
        response: Dict[str, Any],
        request_id: str,
        tool_name: str,
        timestamp: str
    ) -> Dict[str, Any]:
        """Normalize MCP server response.
        
        Args:
            response (dict): Raw response from MCP server.
            request_id (str): Request ID.
            tool_name (str): Tool name.
            timestamp (str): Request timestamp.
            
        Returns:
            dict: Normalized response.
        """
        if "error" in response:
            error_data = response["error"]
            return {
                "success": False,
                "error": {
                    "code": error_data.get("code", "UNKNOWN_ERROR"),
                    "message": error_data.get("message", "Unknown error occurred"),
                    "data": error_data.get("data")
                },
                "request_id": request_id,
                "tool_name": tool_name,
                "timestamp": timestamp
            }
        
        if "result" in response:
            return {
                "success": True,
                "result": response["result"],
                "request_id": request_id,
                "tool_name": tool_name,
                "timestamp": timestamp
            }
        
        return {
            "success": False,
            "error": {
                "code": "INVALID_RESPONSE",
                "message": "Response missing both 'result' and 'error' fields",
                "data": response
            },
            "request_id": request_id,
            "tool_name": tool_name,
            "timestamp": timestamp
        }
    
    def disconnect(self) -> None:
        """Close connection to MCP server."""
        if self._is_open:
            self._connector.close()
            self._is_open = False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
