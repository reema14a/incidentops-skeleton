# MCP Client Structured Exceptions

## Overview

The MCP Client provides a comprehensive set of structured exceptions that include error codes, contextual information, and serialization capabilities for robust error handling and logging.

## Exception Hierarchy

```
MCPError (base)
├── MCPConnectionError
├── MCPToolError
├── MCPTimeoutError
├── MCPConfigurationError
└── MCPResponseError
```

## Base Exception: MCPError

All MCP exceptions inherit from `MCPError`, which provides:

- **message**: Human-readable error description
- **error_code**: Machine-readable error code for programmatic handling
- **context**: Dictionary with additional error context
- **to_dict()**: Method to serialize exception for logging
- **__str__()**: Formatted string representation with error code

### Example Usage

```python
from llm.mcp_client import MCPClient, MCPError

try:
    client = MCPClient()
    response = client.call_tool("gmail.send", params)
except MCPError as e:
    print(f"Error: [{e.error_code}] {e.message}")
    print(f"Context: {e.context}")
    
    # Serialize for logging
    error_dict = e.to_dict()
    logger.error("MCP operation failed", extra=error_dict)
```

## Exception Types

### MCPConnectionError

Raised when connection to MCP server fails.

**Error Codes:**
- `MCP_CONNECTION_ERROR` (default)
- `MCP_CONNECTION_FAILED`

**Context Fields:**
- `endpoint`: The endpoint that failed to connect
- `retry_count`: Number of retry attempts made
- `all_attempts_failed`: Boolean indicating if all retries exhausted

**Common Causes:**
- Network unreachable
- Invalid endpoint URL
- Server not responding
- Firewall blocking connection

### MCPToolError

Raised when tool invocation fails.

**Error Codes:**
- `MCP_TOOL_ERROR` (default)
- `MCP_TOOL_<SERVER_CODE>` (e.g., `MCP_TOOL_INVALID_PARAMS`)
- `MCP_REQUEST_FAILED`
- `MCP_RECONNECTION_FAILED`

**Context Fields:**
- `tool_name`: Name of the tool that failed
- `request_id`: Unique request identifier for tracing
- `server_error`: Error response from MCP server (if available)

**Common Causes:**
- Invalid tool parameters
- Tool not found
- Authentication failure
- Rate limiting
- Server-side execution error

### MCPTimeoutError

Raised when operations exceed timeout limits.

**Error Code:**
- `MCP_TIMEOUT_ERROR`

**Context Fields:**
- `timeout_seconds`: Timeout duration that was exceeded
- `operation`: Operation that timed out (e.g., "connect", "tool_invocation")

**Common Causes:**
- Slow network connection
- Server overload
- Large response payload
- Timeout configured too short

### MCPConfigurationError

Raised when configuration is invalid or missing.

**Error Codes:**
- `MCP_CONFIGURATION_ERROR` (default)
- `MCP_DEPENDENCY_MISSING`

**Context Fields:**
- `config_key`: Configuration key that is invalid/missing
- `config_file`: Configuration file path
- `required_package`: Missing dependency package (if applicable)

**Common Causes:**
- Missing MCP endpoint configuration
- Invalid configuration values
- Missing websocket-client library
- Configuration file not found

### MCPResponseError

Raised when server response is invalid or malformed.

**Error Code:**
- `MCP_RESPONSE_ERROR`

**Context Fields:**
- `response_data`: Raw response data (truncated to 200 chars)
- `expected_format`: Expected response format (e.g., "JSON")
- `tool_name`: Tool that generated the response
- `request_id`: Request identifier

**Common Causes:**
- Invalid JSON in response
- Missing required response fields
- Unexpected response format
- Corrupted data transmission

## Error Handling Patterns

### Pattern 1: Specific Error Handling

```python
from llm.mcp_client import (
    MCPClient,
    MCPConfigurationError,
    MCPConnectionError,
    MCPToolError
)

client = MCPClient()

try:
    response = client.call_tool("gmail.send", params)
    
except MCPConfigurationError as e:
    print(f"Configuration issue: {e.message}")
    print(f"Please set {e.context['config_key']} in {e.context['config_file']}")
    
except MCPConnectionError as e:
    if e.context.get('all_attempts_failed'):
        print(f"Failed after {e.context['retry_count']} attempts")
        # Implement fallback logic
    
except MCPToolError as e:
    server_error = e.context.get('server_error', {})
    if server_error.get('code') == 'INVALID_PARAMS':
        print("Invalid parameters provided")
    elif server_error.get('code') == 'AUTH_FAILED':
        print("Authentication failed")
```

### Pattern 2: Structured Logging

```python
import json
from llm.mcp_client import MCPClient, MCPError

try:
    client = MCPClient()
    response = client.call_tool("pushover.send", params)
    
except MCPError as e:
    # Convert to dictionary for structured logging
    error_dict = e.to_dict()
    
    # Log as JSON
    logger.error(
        "MCP operation failed",
        extra={
            "error_type": error_dict["error_type"],
            "error_code": error_dict["error_code"],
            "message": error_dict["message"],
            "context": error_dict["context"]
        }
    )
```

### Pattern 3: Error Recovery

```python
from llm.mcp_client import (
    MCPClient,
    MCPTimeoutError,
    MCPConnectionError
)

def send_notification_with_fallback(message):
    client = MCPClient()
    
    try:
        return client.call_tool("gmail.send", {"message": message})
        
    except MCPTimeoutError as e:
        print(f"Timeout after {e.context['timeout_seconds']}s, retrying...")
        # Retry with longer timeout
        client.timeout = e.context['timeout_seconds'] * 2
        return client.call_tool("gmail.send", {"message": message})
        
    except MCPConnectionError as e:
        print("MCP unavailable, using fallback notification method")
        return send_via_fallback_method(message)
```

## Testing with Structured Exceptions

```python
import pytest
from llm.mcp_client import MCPToolError

def test_tool_error_structure():
    """Test that MCPToolError includes all expected fields."""
    error = MCPToolError(
        "Tool failed",
        error_code="MCP_TOOL_EXECUTION_ERROR",
        tool_name="gmail.send",
        request_id="req-123"
    )
    
    # Test attributes
    assert error.error_code == "MCP_TOOL_EXECUTION_ERROR"
    assert error.message == "Tool failed"
    assert error.context["tool_name"] == "gmail.send"
    assert error.context["request_id"] == "req-123"
    
    # Test serialization
    error_dict = error.to_dict()
    assert error_dict["error_type"] == "MCPToolError"
    assert "context" in error_dict
    
    # Test string representation
    assert "[MCP_TOOL_EXECUTION_ERROR]" in str(error)
```

## Best Practices

1. **Always catch specific exceptions first**: Handle specific exception types before the generic `MCPError`

2. **Use error codes for programmatic handling**: Check `error_code` for specific error conditions rather than parsing error messages

3. **Log structured error information**: Use `to_dict()` to serialize exceptions for structured logging systems

4. **Include context in error reports**: The `context` dictionary provides valuable debugging information

5. **Implement appropriate fallbacks**: Use exception context to determine the best recovery strategy

6. **Don't swallow exceptions**: Always log or handle exceptions appropriately

7. **Test error scenarios**: Write tests that verify exception handling for different error conditions

## Migration from Previous Error Handling

If you have existing code using the old exception classes, the migration is straightforward:

**Before:**
```python
try:
    client.call_tool("gmail.send", params)
except MCPConnectionError as e:
    print(f"Connection failed: {e}")
```

**After (enhanced):**
```python
try:
    client.call_tool("gmail.send", params)
except MCPConnectionError as e:
    print(f"Connection failed: [{e.error_code}] {e.message}")
    print(f"Endpoint: {e.context['endpoint']}")
    print(f"Retries: {e.context['retry_count']}")
```

The old code will continue to work, but you can now access additional structured information through the `error_code` and `context` attributes.
