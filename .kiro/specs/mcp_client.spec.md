---
name: MCP Client Wrapper
status: draft
description: A unified MCP client supporting both standard WebSocket-based MCP servers and viaSocket's HTTP/S-based MCP transport. Includes cleanup of previous WebSocket-only implementation and introduction of a new dual-transport architecture.
---

# Overview

The MCPClient enables agents within IncidentOps (most importantly NotificationAgent) to invoke remote MCP tools through a consistent, unified interface. The system supports three MCP transport mechanisms:

1. Standard MCP servers using a native WebSocket endpoint (ws:// or wss://)
2. viaSocket MCP servers using HTTP(S) endpoints with internal upgrade handled by viaSocket
3. viaSocket MCP servers using Server-Sent Events (SSE) endpoints (ending with /sse)

Any previously generated WebSocket-only implementation must be removed and replaced with a clean multi-transport design.

All configuration must originate from SettingsLoader.

# Functional Requirements

## 1. Transport Modes

### A. Standard WebSocket MCP Transport
- Endpoint must begin with `ws://` or `wss://`.
- Use a dedicated WebSocket connector for:
  - connection establishment
  - reconnection
  - sending and receiving MCP messages

### B. viaSocket HTTP/S MCP Transport
- Endpoint must be `http://` or `https://` and must contain `.viasocket.com`.
- The endpoint must not be converted into WebSocket form.
- Use a dedicated viaSocket-compatible connector that:
  - establishes MCP communication via HTTP/S
  - relies on viaSocket’s backend to perform the WebSocket upgrade internally
  - matches the same interface as the WebSocket connector

### C. viaSocket SSE MCP Transport
- Endpoint must end with `/sse` and must contain `.viasocket.com`.
- Use a dedicated SSE connector that:
  - opens a persistent SSE stream for receiving responses
  - sends messages via HTTP POST to a separate `/send` endpoint
  - buffers incoming SSE events in a thread-safe manner
  - provides blocking receive() that polls the buffer
  - matches the same interface as other connectors

## 2. Transport Detection

Transport mode must be selected automatically:

| Condition | Transport |
|----------|-----------|
| endpoint ends with `/sse` | viaSocket SSE MCP |
| endpoint starts with `ws://` or `wss://` | WebSocket |
| endpoint contains `.viasocket.com` (http/https) | viaSocket HTTP MCP |
| otherwise | MCPConfigurationError |

Note: SSE detection takes priority over HTTP detection for viaSocket endpoints.

## 3. MCPClient Unified Public Interface

Agents interact via:

### `call_tool(tool_name, params)`

Responsibilities:
- Construct an MCP-compliant request (ID, tool name, params, timestamp).
- Delegate send/receive to the chosen transport connector.
- Return normalized structured response dicts.
- Never leak raw exceptions.

## 4. Connection Handling

- Lazy or eager connection based on configuration.
- Automatic reconnection upon disconnection.
- Clear structured errors if connection attempts fail.
- Connector classes must isolate transport mechanisms fully.

## 5. Response Handling

- Successful results parsed into Python dictionaries.
- MCP errors returned as structured error objects.
- Unified response structure across both transports.
- No raw library exceptions reach agents.

## 6. Logging Requirements

Log the following:

- Selected transport mode
- Connection successes/failures
- Reconnection attempts
- Sanitized configuration on initialization
- Full request metadata (mask sensitive values)
- Raw and parsed responses
- Structured errors

All logs must adhere to the global logging configuration.

## 7. Configuration Requirements

All configuration must come from SettingsLoader exclusively:

- endpoint (required)
- timeout
- retry_delay
- max_retries
- notification channel flags

Priority follows:
1. Environment variables
2. settings.yaml
3. internal safe defaults

The MCPClient must not read environment variables or YAML.

## 8. Security Requirements

- Mask secrets in logs.
- Accept HTTP endpoints only when domain contains `.viasocket.com`.
- Reject HTTP endpoints for non-viaSocket servers.
- Enforce strict endpoint validation.

# Implementation Requirements

## 1. Connector Architecture

Implement two connector classes with identical method signatures:

### `MCPWebSocketConnector`
- Handles ws:// and wss:// endpoints
- Implements:
  - open
  - close
  - reconnect
  - send
  - receive

### `MCPViaSocketHTTPConnector`
- Handles http:// and https:// endpoints containing `.viasocket.com`
- Implements:
  - open
  - close (if applicable)
  - send
  - receive
  - reconnection semantics as supported by viaSocket

### `MCPViaSocketSSEConnector`
- Handles endpoints ending with `/sse` and containing `.viasocket.com`
- Implements:
  - open (starts SSE stream and background reader thread)
  - close (stops stream and thread)
  - send (HTTP POST to `/send` endpoint)
  - receive (blocking poll from response buffer)
  - reconnect (with retry logic)

All connectors must conform to a shared abstract interface for transport operations.

## 2. MCPClient Orchestration

MCPClient must:

- Read the endpoint from SettingsLoader.
- Detect transport mode.
- Instantiate the appropriate connector.
- Proxy all public calls through the connector.
- Maintain consistent request/response formatting.

# Tasks

## Cleanup & Refactor Tasks (REQUIRED)
- [x] Remove any previously generated WebSocket-only MCP client logic from `llm/mcp_client.py`.
- [x] Remove outdated WebSocket-only helper methods, reconnection logic, and protocol assumptions.
- [x] Remove or refactor existing unit tests that assume WebSocket-only transport.
- [x] Remove direct YAML/env reads inside the MCPClient if previously generated.

## Core Implementation Tasks
- [x] Implement transport detection based on endpoint.
- [x] Implement `MCPWebSocketConnector`.
- [x] Implement `MCPViaSocketHTTPConnector`.
- [x] Implement `MCPViaSocketSSEConnector`.
- [x] Implement `MCPClient` with dynamic transport selection and unified interface.
- [x] Ensure structured request/response formatting across all connectors.

## Configuration Tasks
- [x] Integrate SettingsLoader and remove all direct env/yaml access.
- [x] Add configuration validation for both transport modes.
- [x] Log sanitized effective configuration at startup.

## Logging Tasks
- [x] Log selected transport mode.
- [x] Log all connection and reconnection events.
- [x] Log all tool invocations and their responses (with masking).
- [x] Log structured errors from both connectors.

## Testing Tasks
- [x] Add mocks and tests for WebSocket transport.
- [x] Add mocks and tests for viaSocket HTTP/S transport.
- [x] Add mocks and tests for viaSocket SSE transport.
- [x] Test automatic transport detection.
- [x] Test structured error flow.
- [x] Test reconnection logic for all connectors.
- [x] Test rejection of invalid endpoint formats.

# Acceptance Criteria

- MCPClient initializes correctly under all three transport modes.
- Tool invocation works end-to-end for:
  - WebSocket-based MCP servers
  - viaSocket HTTP-based MCP servers
  - viaSocket SSE-based MCP servers
- No remnants of WebSocket-only architecture remain.
- Response formats are consistent and structured across all transports.
- No direct access to env/yaml within MCPClient.
- SettingsLoader is the sole configuration source.
- Tests cover all transport paths and error scenarios.
- NotificationAgent successfully uses the MCPClient in all modes.

# Notes for Kiro

- Maintain strict separation of transport logic into connector classes.
- Follow project import rules and steering guidelines.
- Implement incrementally but ensure final structure follows the spec.
- Avoid mixing WebSocket and viaSocket transport primitives.
