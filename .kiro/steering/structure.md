---
inclusion: always
---

# Project Structure

## Directory Organization

```
├── agents/           # Agent implementations
├── config/           # YAML configuration files
├── data/             # Data directory
    └── db/           # Persistent database files (SQLite)
    └── samples/      # Sample input logs, demo logs
    └── output/       # Optional pipeline output dumps
├── db/               # Database utilities
├── hooks/            # MCP integration hooks
├── llm/              # LLM files
    └── local_mcp/    # Local MCP server
    └── mcp_client/   # MCP client 
├── logs/             # Runtime logs (pipeline.log, mcp_server.log)
├── orchestrator/     # Pipeline orchestration logic
├── tests/            
    └── unit/         # Pure unit tests for individual agents
    └── integration/  # Multi-agent flows and full pipeline tests 
├── ui/               # User interface (console client)
└── utils/            # Shared utilities

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

## Data Directory Structure

### data/db/
Persistent database files (SQLite):
- `incidents.db` - Main incident storage
- Other persistent data stores

### data/samples/
Sample input files for testing and demonstration:
- `sample_logs.txt` - Example log entries
- Other demo/test input files

### data/output/
Optional pipeline output dumps:
- `output_log.json` - JSON output from pipeline runs
- Other generated artifacts

## Logging Structure
All runtime logs are written to the `logs/` directory at project root:
```
logs/pipeline.log      # Agent pipeline execution logs
logs/mcp_server.log    # MCP server logs
```

**Log Path Configuration:**
- Pipeline logs: Hardcoded in `agents/base_agent.py` (line ~30)
- MCP server logs: Hardcoded in `llm/local_mcp/server.py`
- Log directory is created automatically if it doesn't exist
- Uses rotating file handlers (5MB max, 3 backups)

**Note**: Runtime logs are kept at project root (not under `data/`) following common conventions. This separates transient runtime logs from persistent data.

## Database Storage
- Database files stored in `data/db/`
- Avoid inline SQL anywhere outside `db/db_util.py`
- If a spec defines a storage layer, only that module may interact with the database
- All DB writes must go through the DB utility module
- Kiro must never generate DB write/SQL code inside agents directly
