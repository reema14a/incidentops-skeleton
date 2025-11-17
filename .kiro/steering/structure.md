---
inclusion: always
---

# Project Structure

## Directory Organization

```
├── agents/           # Agent implementations
├── config/           # YAML configuration files
├── data/             # Sample data and output logs
├── hooks/            # MCP integration hooks
├── llm/              # LLM files
    └── local_mcp/    # Local MCP server
    └── mcp_client/   # MCP client 
├── orchestrator/     # Pipeline orchestration logic
├── tests/            
    └── unit/         # Pure unit tests for individual agents
    └── integration/  # Multi-agent flows and full pipeline tests 
├── ui/               # User interface (console client)
└── util/             # Shared utilities

```

## Agent Architecture

All agents inherit from `BaseAgent` class in `agents/base_agent.py`:

- Each agent must implement `run(input_data=None)` method
- Use `self.log(message)` for consistent logging format
- Agent names should be descriptive and passed to constructor
- Agents are stateless and process data in a pipeline

## Naming Conventions

- **Files**: Snake_case (e.g., `monitor_agent.py`)
- **Classes**: PascalCase with "Agent" suffix (e.g., `MonitorAgent`)
- **Methods**: Snake_case (e.g., `run_pipeline()`)
- **Config files**: Lowercase with underscores (e.g., `settings.yaml`)

## Configuration Pattern

- Runtime settings in `config/settings.yaml`
- Pipeline definitions in `config/workflows.yaml`
- Agent sequence defined declaratively in workflows
- Paths configurable via settings (default: `data/` directory)

## Hook Integration

Hooks in `hooks/` directory provide external integrations:
- `alert_api_hook.py` - Alert system integration
- `jira_hook.py` - Issue tracking integration
- `metrics_hook.py` - Metrics parsing and monitoring

## Code Style

- Simple, readable Python
- Minimal dependencies
- Clear separation between agent logic and orchestration
- Logging format: `[AgentName] message`

## Tests Directory

```
tests/             # Unit and integration tests for agents, hooks, orchestrator
  unit/            # Pure unit tests for individual agents
    test_monitor.py
    test_triage.py
    test_llm_alert_summary.py
    test_llm_resolution.py
    test_llm_governance.py
    test_notification.py
    test_opslog.py
    test_orchestrator.py
    test_settings_loader.py
    test_config_validation.py
    test_notification_mcp_errors.py
  integration/     # Multi-agent flows and full pipeline tests
    test_monitor_to_llm_summary.py
    test_notification_pipeline_integration.py
  mcp_client/      # MCP client tests
    test_basic_success.py
  local_mcp_server/  # Local MCP server tests
    test_router.py
    test_gmail_tool.py
    test_pushover_tool.py
    test_jsonrpc_compliance.py
  e2e/             # End-to-end full pipeline tests
    test_full_roundtrip.py
    test_notification_delivery_e2e.py

```
Rules: 
- Kiro should place all permanent test files here.  
- Temporary validation tests created during task execution should be retained as real tests under this directory.
- Kiro must generate unit tests inside tests/unit/.
- Kiro must generate integration tests inside tests/integration/.
- Kiro must generate MCP client tests inside tests/mcp_client/.
- Kiro must generate local MCP server tests inside tests/local_mcp_server/.
- Kiro must generate end-to-end pipeline tests inside tests/e2e/.
- Unit tests must not perform file I/O or run the pipeline.
- Integration tests may exercise pipeline execution or multi-agent flows.
- E2E tests should test the complete system from end to end.
- Integration tests may exercise pipeline execution or multi-agent flows.

## Shared Utilities

- JSON extraction helper
```
utils/json_parser.py
```

## Logging Structure
All runtime logs must be written to:
```
logs/pipeline.log
```
The logs directory is located at the project root and stores all pipeline logs for debugging, audit, and demonstration.
