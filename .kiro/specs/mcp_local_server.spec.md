---
name: Local MCP Server
status: draft
description: A minimal local HTTP MCP server for IncidentOps that exposes gmail.send and pushover.send tools for NotificationAgent.

---

## Overview

This spec defines a simple local HTTP-based MCP server that replaces viaSocket/SSE/WebSocket complexity. It exposes two tools (gmail.send and pushover.send) and responds through a JSON-RPC 2.0 compliant POST endpoint. NotificationAgent will use this server for all notification delivery.

## Server Architecture

- Server location: llm/local_mcp/
- Entrypoint: llm/local_mcp/server.py
- Run URL: [http://localhost:5005](http://localhost:5005)

### Endpoints

* POST /send

  - Accepts JSON-RPC 2.0 requests using method = "tools/call"
  - params.name maps to tool name
  - params.arguments holds tool parameters
  - Returns JSON-RPC response with "result" for success or "error" for failure

### Response Format

- Success response contains: jsonrpc, id, result
- Error response contains: jsonrpc, id, error (code, message, optional data)

## Tools to Implement

### gmail.send

- Parameters: to, subject, body
- Uses SettingsLoader.get_secret for Gmail credentials
- Sends email using SMTP or Gmail API (implementation choice)
- Note: Gmail requires a 16-character App Password for SMTP, not your Google account password. 
  - Environment variables required:
    - GMAIL_USER
    - GMAIL_PASSWORD  # Gmail App Password

### pushover.send

- Parameters: user, message, title, priority
- Uses SettingsLoader.get_secret for PUSHOVER_USER_KEY
- Calls Pushover REST API

## Restrictions

- Never log secrets
- Log request id, tool name, timestamp
- JSON-RPC structure must always match spec

## Directory Layout

- llm/local_mcp/server.py
- llm/local_mcp/router.py
- llm/local_mcp/tools/gmail_tool.py
- llm/local_mcp/tools/pushover_tool.py

## Testing Requirements

- All tests must go under:
    - tests/e2e/
    - tests/local_mcp_server/
- Mock SMTP and Pushover API
- Test happy path and error cases

## Tasks

### Core Server Implementation Tasks

- [x] Create server.py with a JSON-RPC POST /send handler
- [x] Create router to map params.name to tool implementations
- [x] Implement gmail_tool and pushover_tool
- [x] Use SettingsLoader.get_secret for credentials
- [x] Ensure JSON-RPC compliance in every response

### Configuration Tasks

- [ ] Update settings.yaml default endpoint for MCP to [http://localhost:5005/send](http://localhost:5005/send)

### Validation Tasks

- [ ] Generate tests for:
  - MCP router (success + missing tool)
  - Gmail tool (mock SMTP)
  - Pushover tool (mock requests)
  - Full E2E roundtrip: MCPClient → Local MCP Server → tool

- [ ] Make NotificationAgent send gmail and pushover notifications successfully through local server
- [ ] Ensure consistent logging without exposing secrets

### Acceptance Criteria

- NotificationAgent end-to-end notification flow works using local MCP server
- All tests for server and tools pass
- No SSE or WebSocket code remains in the repository

---
