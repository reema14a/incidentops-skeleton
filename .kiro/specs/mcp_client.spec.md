---
name: MCP Client (HTTP Only)
status: draft
description: A simplified HTTP-only MCPClient that posts JSON-RPC to the local MCP server.
---
## Overview

This spec replaces the multi-transport MCP client with a simple HTTP-only version. It sends POST requests to the local MCP server endpoint configured in settings and receives JSON-RPC 2.0 responses.

## Functional Responsibilities

### MCPClient Initialization

- MCPClient(endpoint=None, timeout=30, retry_delay=2, max_retries=3)
- Default endpoint loaded from settings.notification.mcp.endpoint

### Behavior

call_tool(tool_name, params):

1. Generates JSON-RPC request (id, method "tools/call", params)
2. Sends POST to configured endpoint
3. Parses JSON-RPC response
4. Returns normalized result

### Normalized Response Format

On success:

- success = true
- result = {...}
- request_id
- tool_name
- timestamp

On error:

- success = false
- error = code, message, data
- request_id
- tool_name
- timestamp

### Exceptions Required

- MCPConnectionError
- MCPToolError
- MCPTimeoutError
- MCPResponseError
- MCPConfigurationError

### Logging Requirements

- Log tool name, request id, endpoint, timestamp
- Mask secrets
- Log truncated raw responses

### Validation Rules

- Endpoint must begin with http:// or https://
- JSON-RPC response must contain either result or error
- Timeout behavior must be enforced

## Tests to Implement

- tests/mcp_client/test_basic_success.py
- tests/mcp_client/test_error_response.py
- tests/mcp_client/test_network_failure.py

## Tasks

### Cleanup Tasks

- [x] Delete all connector classes: MCPViaSocketSSEConnector, MCPViaSocketHTTPConnector, MCPWebSocketConnector
- [x] Delete detection helpers and related legacy tests
- [x] Remove any SSE/WebSocket logic from NotificationAgent

### Core Implementation Tasks

- [x] Implement single HTTP-based MCPClient using requests.post
- [x] Ensure retries follow retry_delay and max_retries
- [x] Ensure strict JSON-RPC format on responses
- [x] Wire NotificationAgent to use the updated client

### Integration Tasks

- [x] Test NotificationAgent calling the local MCP server for gmail and pushover
- [x] Confirm full end-to-end flow works

### Acceptance Criteria

- MCPClient has no multi-transport logic
- All tests for client pass
- NotificationAgent functions using only HTTP POST to local server

---
