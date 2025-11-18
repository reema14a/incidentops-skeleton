# Test Directory Reorganization

## Overview

The test directory has been reorganized to follow a more structured approach that separates tests by their purpose and scope, as defined in `.kiro/steering/structure.md`.

## New Structure

```
tests/
├── unit/                    # Pure unit tests for individual agents
│   ├── test_monitor.py
│   ├── test_triage.py
│   ├── test_llm_alert_summary.py
│   ├── test_llm_resolution.py
│   ├── test_llm_governance.py
│   ├── test_notification.py
│   ├── test_opslog.py
│   ├── test_orchestrator.py
│   ├── test_settings_loader.py
│   ├── test_config_validation.py
│   └── test_notification_mcp_errors.py
├── integration/             # Multi-agent flows and pipeline tests
│   ├── test_monitor_to_llm_summary.py
│   └── test_notification_pipeline_integration.py
├── mcp_client/              # MCP client tests
│   └── test_basic_success.py
├── local_mcp_server/        # Local MCP server tests
│   ├── test_router.py
│   ├── test_gmail_tool.py
│   ├── test_pushover_tool.py
│   └── test_jsonrpc_compliance.py
└── e2e/                     # End-to-end full pipeline tests
    ├── test_full_roundtrip.py
    └── test_notification_delivery_e2e.py
```

## Changes Made

### Files Moved

| Original Location | New Location | Reason |
|------------------|--------------|--------|
| `tests/unit/test_local_mcp_router.py` | `tests/local_mcp_server/test_router.py` | MCP server component |
| `tests/unit/test_gmail_tool.py` | `tests/local_mcp_server/test_gmail_tool.py` | MCP server tool |
| `tests/unit/test_pushover_tool.py` | `tests/local_mcp_server/test_pushover_tool.py` | MCP server tool |
| `tests/integration/test_mcp_server_jsonrpc_compliance.py` | `tests/local_mcp_server/test_jsonrpc_compliance.py` | MCP server compliance |
| `tests/unit/test_mcp_client.py` | `tests/mcp_client/test_basic_success.py` | MCP client component |
| `tests/integration/test_full_pipeline.py` | `tests/e2e/test_full_roundtrip.py` | End-to-end test |
| `tests/integration/test_notification_delivery_e2e.py` | `tests/e2e/test_notification_delivery_e2e.py` | End-to-end test |

### Directory Purposes

1. **tests/unit/** - Pure unit tests for individual agents
   - Tests single components in isolation
   - Uses mocks for dependencies
   - No file I/O or pipeline execution

2. **tests/integration/** - Multi-agent flows and pipeline tests
   - Tests interactions between multiple agents
   - May execute partial pipeline flows
   - Tests integration points

3. **tests/mcp_client/** - MCP client tests
   - Tests for the MCP client implementation
   - Tests different transport mechanisms (WebSocket, HTTP, SSE)
   - Tests error handling and connection management

4. **tests/local_mcp_server/** - Local MCP server tests
   - Tests for the local MCP server implementation
   - Tests tool routing and execution
   - Tests JSON-RPC 2.0 compliance
   - Tests individual tools (gmail, pushover)

5. **tests/e2e/** - End-to-end full pipeline tests
   - Tests complete system from start to finish
   - Tests full pipeline execution
   - Tests notification delivery flows

## Running Tests

### Run all tests
```bash
python -m pytest tests/ -v
```

### Run tests by category
```bash
# Unit tests only
python -m pytest tests/unit/ -v

# Integration tests only
python -m pytest tests/integration/ -v

# MCP client tests
python -m pytest tests/mcp_client/ -v

# Local MCP server tests
python -m pytest tests/local_mcp_server/ -v

# End-to-end tests
python -m pytest tests/e2e/ -v
```

### Run specific test files
```bash
# JSON-RPC compliance tests
python -m pytest tests/local_mcp_server/test_jsonrpc_compliance.py -v

# Full pipeline test
python -m pytest tests/e2e/test_full_roundtrip.py -v
```

## Benefits of New Structure

1. **Clear Separation** - Tests are organized by scope and purpose
2. **Easy Navigation** - Developers can quickly find relevant tests
3. **Targeted Testing** - Run only the tests you need during development
4. **Better Maintainability** - Related tests are grouped together
5. **Scalability** - Easy to add new test categories as the project grows

## Guidelines for Adding New Tests

- **Unit tests** → `tests/unit/` - Test individual agents or components
- **Integration tests** → `tests/integration/` - Test multi-agent interactions
- **MCP client tests** → `tests/mcp_client/` - Test MCP client functionality
- **MCP server tests** → `tests/local_mcp_server/` - Test local MCP server
- **E2E tests** → `tests/e2e/` - Test complete system flows

## Verification

All tests pass after reorganization:
- ✅ 25 tests in `tests/local_mcp_server/` - All passing
- ✅ Tests can be run from new locations
- ✅ No import errors or path issues
- ✅ Documentation updated to reflect new structure
