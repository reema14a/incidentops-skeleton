---
inclusion: always
---

# Tech Stack

## Language & Runtime

- **Python 3.10+** - Primary language for all agent logic
- Use type hints where appropriate for clarity

## Dependencies

Core libraries (see `requirements.txt`):
- `python-dotenv` - Environment configuration
- `pyyaml` - YAML config parsing
- `requests` - HTTP integrations
- `gradio` - Optional UI/dashboard

## Configuration

- **YAML** for all agent and workflow definitions
- Config files in `config/` directory:
  - `settings.yaml` - Runtime settings, paths, log levels
  - `workflows.yaml` - Agent pipeline sequences

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the main pipeline
python ui/console_client.py

# Run orchestrator directly
python -c "from orchestrator.orchestrator import run_pipeline; run_pipeline()"
```

## Integration Points

- **MCP Hooks** - Used for log parsing and alert simulation
- **JSON logs** - Output format for governance and traceability
- Output logs stored in `data/output_log.json` (configurable in settings.yaml)
