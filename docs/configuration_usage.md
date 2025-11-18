# Configuration Usage Guide

## Settings Loader

The `SettingsLoader` provides simplified configuration management with environment variable interpolation.

### Basic Usage

```python
from config.settings_loader import get_settings

settings = get_settings()

# Access configuration using dot-notation
endpoint = settings.notification.mcp.endpoint
timeout = settings.notification.mcp.timeout
log_level = settings.runtime.log_level
```

### Environment Variable Interpolation

The `settings.yaml` file supports `${VAR_NAME}` syntax for environment variable expansion:

```yaml
notification:
  mcp:
    endpoint: ${MCP_ENDPOINT}  # Expands to env var value
    timeout: 30  # Can be overridden by MCP_TIMEOUT env var
```

### Configuration Priority

1. **Environment variables** (highest priority)
2. **settings.yaml** values
3. No defaults - configuration must be explicit

### Secret Access

Secrets must ONLY come from environment variables:

```python
# Access any secret
api_key = settings.get_secret('OPENAI_API_KEY')
pushover_key = settings.get_secret('PUSHOVER_USER_KEY')
gmail = settings.get_secret('GMAIL_RECIPIENT')
```

Never store secrets in YAML files!

## Prompt Templates

Prompts are stored in `config/prompts.yaml` and loaded using the prompt loader utility.

### Loading Prompts

```python
from utils.prompt_loader import load_prompt, load_prompt_with_vars

# Load a simple prompt
prompt = load_prompt('alert_summary_prompt')

# Load with variable substitution
prompt = load_prompt_with_vars(
    'alert_summary_prompt',
    alerts='[{"severity": "high", "message": "CPU usage"}]'
)
```

### Available Prompts

- `alert_summary_prompt` - Summarize system alerts
- `resolution_prompt` - Generate resolution plans
- `governance_prompt` - Governance and compliance audit

### Adding New Prompts

Edit `config/prompts.yaml`:

```yaml
my_new_prompt: |
  You are an AI assistant. Analyze the following:
  {input_data}
  
  Provide a structured response.
```

Then use it:

```python
prompt = load_prompt_with_vars('my_new_prompt', input_data='...')
```

## Environment Variables

All environment variables should be documented in `.env.example`:

### Required Variables

- `MCP_ENDPOINT` - MCP server endpoint (WebSocket or viaSocket HTTP)
- `OPENAI_API_KEY` - OpenAI API key (secret)

### Optional Variables

- `MCP_TIMEOUT` - Connection timeout (default: 30)
- `MCP_MAX_RETRIES` - Max retry attempts (default: 3)
- `MCP_RETRY_DELAY` - Delay between retries (default: 2)
- `LOG_LEVEL` - Logging level (default: INFO)
- `ENABLE_HOOKS` - Enable hooks (default: true)
- `SAVE_OUTPUT` - Save output logs (default: true)
- `USE_REAL_OPENAI` - Use real OpenAI API (default: false)
- `DATA_DIR` - Data directory (default: data/)
- `OUTPUT_LOG_PATH` - Output log path (default: data/output_log.json)
- `NOTIFICATION_CHANNELS` - Comma-separated channels
- `PUSHOVER_USER_KEY` - Pushover key (secret)
- `GMAIL_RECIPIENT` - Gmail recipient (secret)

## Best Practices

1. **Use dot-notation** for all configuration access
2. **Never hardcode secrets** - always use environment variables
3. **Keep prompts in prompts.yaml** - don't embed them in code
4. **Document new env vars** in `.env.example`
5. **Use type conversion** - the loader handles int/bool conversion automatically
