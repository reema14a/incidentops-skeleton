# Local MCP Server JSON-RPC 2.0 Compliance

## Overview

The Local MCP Server implements full JSON-RPC 2.0 specification compliance for all request and response handling. This document describes the implementation details and validation approach.

## JSON-RPC 2.0 Specification

The server follows the [JSON-RPC 2.0 specification](https://www.jsonrpc.org/specification) which defines:

### Request Format
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "gmail.send",
    "arguments": {...}
  },
  "id": 1
}
```

### Success Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {...}
}
```

### Error Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "Optional additional error information"
  }
}
```

## Implementation Details

### Error Codes

The server implements all standard JSON-RPC 2.0 error codes:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | JSON-RPC structure invalid |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal server error |

### Error Handling

The `JSONRPCError` class in `llm/local_mcp/server.py` provides:

1. **Error code constants** - Predefined error codes matching the spec
2. **Error response builder** - `create_error_response()` method that ensures proper structure
3. **Consistent formatting** - All errors follow the same structure

### Request Validation

The server validates every request for:

1. **Valid JSON** - Malformed JSON returns parse error (-32700)
2. **JSON object** - Request must be an object, not array or primitive
3. **jsonrpc field** - Must be present and equal to "2.0"
4. **method field** - Must be "tools/call" for this server
5. **params structure** - Must be an object with required fields
6. **ID preservation** - Request ID is preserved in response (can be string, number, or null)

### Response Guarantees

Every response from the server guarantees:

1. **jsonrpc field** - Always "2.0"
2. **id field** - Matches request ID (null for parse errors)
3. **Mutual exclusivity** - Either `result` OR `error`, never both
4. **Error structure** - Errors always have `code` and `message`, optionally `data`
5. **Success structure** - Success responses always have `result` field

## Testing

Comprehensive integration tests validate JSON-RPC compliance in `tests/local_mcp_server/test_jsonrpc_compliance.py`:

### Test Coverage

- ✅ Parse error responses (invalid JSON)
- ✅ Invalid request errors (missing/wrong jsonrpc version)
- ✅ Method not found errors
- ✅ Invalid params errors (missing tool name, unknown tool)
- ✅ Success response structure
- ✅ Internal error responses
- ✅ ID preservation (string, number, null)
- ✅ Non-object request/params handling
- ✅ Error code constants validation
- ✅ Error response builder validation

### Running Tests

```bash
# Run JSON-RPC compliance tests
python -m pytest tests/local_mcp_server/test_jsonrpc_compliance.py -v

# Run all MCP server tests
python -m pytest tests/local_mcp_server/ -v
```

## Examples

### Successful Tool Call

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "gmail.send",
    "arguments": {
      "to": "user@example.com",
      "subject": "Alert",
      "body": "System alert message"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true,
    "message": "Email sent to user@example.com",
    "recipient": "user@example.com",
    "subject": "Alert"
  }
}
```

### Error: Unknown Tool

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "unknown.tool",
    "arguments": {}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Unknown tool: unknown.tool. Supported tools: gmail.send, pushover.send"
  }
}
```

### Error: Parse Error

**Request:**
```
{invalid json
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32700,
    "message": "Parse error",
    "data": "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"
  }
}
```

## Compliance Checklist

- ✅ All responses include `jsonrpc: "2.0"`
- ✅ All responses include `id` field matching request
- ✅ Success responses have `result`, never `error`
- ✅ Error responses have `error`, never `result`
- ✅ Error objects have `code` and `message`
- ✅ Error codes follow JSON-RPC 2.0 standard
- ✅ Parse errors use `id: null`
- ✅ Request IDs preserved exactly (string, number, null)
- ✅ Invalid JSON returns parse error
- ✅ Invalid structure returns invalid request error
- ✅ Unknown methods return method not found error
- ✅ Invalid parameters return invalid params error
- ✅ Tool execution failures return appropriate errors

## References

- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
- Server implementation: `llm/local_mcp/server.py`
- Compliance tests: `tests/local_mcp_server/test_jsonrpc_compliance.py`
