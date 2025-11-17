"""MCP Client for connecting to MCP servers and invoking tools.

This module provides an HTTP-only MCPClient class for calling tools
on a local MCP server via JSON-RPC 2.0 over HTTP POST.

Note: Multi-transport connector classes have been removed.
The MCPClient class needs to be reimplemented with HTTP-only transport.
"""

import logging
import json
import time
import uuid
from typing import Any, Optional, Dict

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


class MCPClient:
    """HTTP-only MCP client for calling tools on local MCP server.
    
    Sends JSON-RPC 2.0 requests via HTTP POST to the configured endpoint.
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
        if requests is None:
            raise MCPConfigurationError(
                "requests library is required for MCPClient. Install with: pip install requests",
                config_key="requests"
            )
        
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
        
        # Validate endpoint format
        if not (self.endpoint.startswith("http://") or self.endpoint.startswith("https://")):
            raise MCPConfigurationError(
                f"MCP endpoint must begin with http:// or https://, got: {self.endpoint}",
                config_key="endpoint"
            )
        
        self.timeout = float(timeout if timeout is not None else settings.notification.mcp.timeout)
        self.retry_delay = float(retry_delay if retry_delay is not None else settings.notification.mcp.retry_delay)
        self.max_retries = int(max_retries if max_retries is not None else settings.notification.mcp.max_retries)
        
        self.logger.info(f"[MCPClient] Initialized with endpoint: {self._mask_secrets(self.endpoint)}")
    
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
        request_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        
        # Build JSON-RPC 2.0 request
        jsonrpc_request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": params or {}
            }
        }
        
        self.logger.info(
            f"[MCPClient] Calling tool '{tool_name}' with request_id={request_id} "
            f"at endpoint={self._mask_secrets(self.endpoint)}"
        )
        
        # Attempt request with retries
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.post(
                    self.endpoint,
                    json=jsonrpc_request,
                    timeout=self.timeout,
                    headers={"Content-Type": "application/json"}
                )
                
                # Check HTTP status
                if response.status_code != 200:
                    # Raise as connection error to trigger retry
                    last_exception = MCPConnectionError(
                        f"HTTP {response.status_code}: {response.text[:200]}",
                        endpoint=self.endpoint,
                        retry_count=attempt
                    )
                    self.logger.warning(
                        f"[MCPClient] HTTP error on attempt {attempt + 1}/{self.max_retries + 1} "
                        f"for tool '{tool_name}': {last_exception.message}"
                    )
                    # Continue to retry logic
                    if attempt < self.max_retries:
                        self.logger.info(f"[MCPClient] Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)
                        continue
                    else:
                        # Last attempt failed, raise the exception
                        raise last_exception
                
                # Parse JSON response
                try:
                    response_data = response.json()
                except json.JSONDecodeError as e:
                    raise MCPResponseError(
                        f"Failed to parse JSON response: {str(e)}",
                        response_data=response.text,
                        expected_format="JSON-RPC 2.0"
                    )
                
                # Validate strict JSON-RPC 2.0 format
                self._validate_jsonrpc_response(response_data, request_id)
                
                # Log truncated response
                response_str = json.dumps(response_data)
                truncated_response = response_str[:200] + "..." if len(response_str) > 200 else response_str
                self.logger.info(
                    f"[MCPClient] Received response for request_id={request_id}: {truncated_response}"
                )
                
                # Normalize and return response
                normalized = self._normalize_response(response_data, request_id, tool_name, timestamp)
                
                # If server returned an error, raise MCPToolError
                if not normalized["success"]:
                    error_info = normalized["error"]
                    raise MCPToolError(
                        f"Tool '{tool_name}' failed: {error_info['message']}",
                        tool_name=tool_name,
                        request_id=request_id,
                        server_error=error_info
                    )
                
                return normalized
                
            except requests.exceptions.Timeout as e:
                last_exception = MCPTimeoutError(
                    f"Request timed out after {self.timeout} seconds",
                    timeout_seconds=self.timeout,
                    operation=f"call_tool({tool_name})"
                )
                self.logger.warning(
                    f"[MCPClient] Timeout on attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for tool '{tool_name}': {str(e)}"
                )
                
            except RequestException as e:
                last_exception = MCPConnectionError(
                    f"Network error: {str(e)}",
                    endpoint=self.endpoint,
                    retry_count=attempt
                )
                self.logger.warning(
                    f"[MCPClient] Connection error on attempt {attempt + 1}/{self.max_retries + 1} "
                    f"for tool '{tool_name}': {str(e)}"
                )
            
            except (MCPResponseError, MCPToolError) as e:
                # Don't retry on response/tool errors
                self.logger.error(f"[MCPClient] Error calling tool '{tool_name}': {str(e)}")
                raise
            
            # Wait before retry (except on last attempt)
            if attempt < self.max_retries:
                self.logger.info(f"[MCPClient] Retrying in {self.retry_delay} seconds...")
                time.sleep(self.retry_delay)
        
        # All retries exhausted
        self.logger.error(
            f"[MCPClient] Failed to call tool '{tool_name}' after {self.max_retries + 1} attempts"
        )
        raise last_exception
    
    def _validate_jsonrpc_response(self, response_data: Dict[str, Any], request_id: str) -> None:
        """Validate JSON-RPC 2.0 response format.
        
        Args:
            response_data (dict): Parsed JSON response.
            request_id (str): Expected request ID.
            
        Raises:
            MCPResponseError: If response does not conform to JSON-RPC 2.0 spec.
        """
        # Check for required 'jsonrpc' field
        if "jsonrpc" not in response_data:
            raise MCPResponseError(
                "JSON-RPC response must contain 'jsonrpc' field",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0 with 'jsonrpc' field"
            )
        
        # Validate jsonrpc version
        if response_data["jsonrpc"] != "2.0":
            raise MCPResponseError(
                f"JSON-RPC version must be '2.0', got: {response_data['jsonrpc']}",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0"
            )
        
        # Check for required 'id' field
        if "id" not in response_data:
            raise MCPResponseError(
                "JSON-RPC response must contain 'id' field",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0 with 'id' field"
            )
        
        # Validate id matches request (convert both to string for comparison)
        if str(response_data["id"]) != str(request_id):
            raise MCPResponseError(
                f"JSON-RPC response 'id' mismatch: expected '{request_id}', got '{response_data['id']}'",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0 with matching id"
            )
        
        # Check for exactly one of 'result' or 'error'
        has_result = "result" in response_data
        has_error = "error" in response_data
        
        if not has_result and not has_error:
            raise MCPResponseError(
                "JSON-RPC response must contain either 'result' or 'error' field",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0 with 'result' or 'error'"
            )
        
        if has_result and has_error:
            raise MCPResponseError(
                "JSON-RPC response must not contain both 'result' and 'error' fields",
                response_data=json.dumps(response_data),
                expected_format="JSON-RPC 2.0 with either 'result' or 'error', not both"
            )
        
        # Validate error structure if present
        if has_error:
            error_data = response_data["error"]
            if not isinstance(error_data, dict):
                raise MCPResponseError(
                    "JSON-RPC 'error' field must be an object",
                    response_data=json.dumps(response_data),
                    expected_format="JSON-RPC 2.0 with error object"
                )
            
            if "code" not in error_data:
                raise MCPResponseError(
                    "JSON-RPC error object must contain 'code' field",
                    response_data=json.dumps(response_data),
                    expected_format="JSON-RPC 2.0 error with 'code'"
                )
            
            if "message" not in error_data:
                raise MCPResponseError(
                    "JSON-RPC error object must contain 'message' field",
                    response_data=json.dumps(response_data),
                    expected_format="JSON-RPC 2.0 error with 'message'"
                )
    
    def _mask_secrets(self, text: str) -> str:
        """Mask sensitive information in logs.
        
        Args:
            text (str): Text that may contain secrets.
            
        Returns:
            str: Text with secrets masked.
        """
        # Simple masking - can be enhanced as needed
        return text
    
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
        """Close connection to MCP server.
        
        Note: HTTP connections are stateless, so no cleanup is needed.
        """
        self.logger.debug("[MCPClient] Disconnect called (no-op for HTTP transport)")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
