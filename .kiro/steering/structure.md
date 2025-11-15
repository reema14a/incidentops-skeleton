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
├── orchestrator/     # Pipeline orchestration logic
├── tests/            
    └── unit/         # Pure unit tests for individual agents
    └── integration/  # Multi-agent flows and full pipeline tests 
└── ui/               # User interface (console client)
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
```
Rules: 
- Kiro should place all permanent test files here.  
- Temporary validation tests created during task execution should be retained as real tests under this directory.
- Kiro must generate unit tests inside tests/unit/.
- Kiro must generate integration tests inside tests/integration/.
- Unit tests must not perform file I/O or run the pipeline.
- Integration tests may exercise pipeline execution or multi-agent flows.

