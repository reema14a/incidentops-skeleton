# Dependency Cleanup - November 17, 2025

## Removed Dependencies

### 1. fastmcp
**Reason:** Not used in the codebase

The project initially included `fastmcp` as a potential MCP framework, but we implemented a custom HTTP-only MCP client and local MCP server instead:
- **MCPClient** (`llm/mcp_client.py`) - Custom HTTP-only client using `requests` library
- **Local MCP Server** (`llm/local_mcp/server.py`) - Custom Flask-based server

No imports or references to `fastmcp` were found in the codebase.

### 2. websocket-client
**Reason:** Not used in the codebase

The `websocket-client` library was likely included for potential WebSocket-based MCP communication, but the final implementation uses HTTP POST only. No imports or references to `websocket` were found in the codebase.

## Verification

All tests pass after removing these dependencies:
- ✅ Full pipeline roundtrip test
- ✅ MCP client unit tests (33 tests)
- ✅ E2E notification delivery tests
- ✅ Local MCP tools tests

## Current Core Dependencies

The project now uses these core dependencies:
- `python-dotenv` - Environment variable management
- `pyyaml` - YAML configuration parsing
- `pytest` - Testing framework
- `requests` - HTTP client for MCP communication
- `openai` - OpenAI API client for LLM agents
- `flask` - Web framework for local MCP server
- `gradio` - Optional UI/dashboard (future use)

## Impact

- Cleaner dependency list
- Faster installation
- No unused code or libraries
- Simpler maintenance
