# Configuration Priority System

## Overview

The IncidentOps SettingsLoader implements a three-tier priority system for configuration management, ensuring flexibility while maintaining security best practices.

## Priority Order

Configuration values are resolved in the following order (highest to lowest priority):

1. **Environment Variables** (highest priority)
2. **settings.yaml** (middle priority)
3. **Secure Defaults** (lowest priority)

## Implementation

The priority system is implemented in `config/settings_loader.py` through the `_get_setting()` method:

```python
def _get_setting(
    self,
    env_key: str,
    yaml_path: List[str],
    default: Any = None,
    required: bool = False,
    secret: bool = False
) -> Any:
    """Get setting with priority: env var > yaml > default."""
    
    # 1. Check environment variable first (highest priority)
    env_value = os.getenv(env_key)
    if env_value is not None:
        return env_value
    
    # 2. Secrets must only come from environment variables
    if secret:
        if required:
            raise ConfigurationError(f"Secret '{env_key}' must be set as environment variable")
        return default
    
    # 3. Check YAML configuration (middle priority)
    yaml_value = self._yaml_config
    for key in yaml_path:
        if isinstance(yaml_value, dict) and key in yaml_value:
            yaml_value = yaml_value[key]
        else:
            yaml_value = None
            break
    
    if yaml_value is not None:
        return yaml_value
    
    # 4. Use default value (lowest priority)
    if required and default is None:
        raise ConfigurationError(f"Required setting '{env_key}' not found")
    
    return default
```

## Configuration Examples

### Example 1: Environment Variable Overrides YAML

**Environment:**
```bash
export MCP_TIMEOUT=90
```

**settings.yaml:**
```yaml
notification:
  mcp:
    timeout: 45
```

**Result:** `get_mcp_timeout()` returns `90` (environment wins)

### Example 2: YAML Overrides Default

**Environment:** (not set)

**settings.yaml:**
```yaml
notification:
  mcp:
    timeout: 45
```

**Default:** `30`

**Result:** `get_mcp_timeout()` returns `45` (YAML wins)

### Example 3: Default Used When Nothing Set

**Environment:** (not set)

**settings.yaml:**
```yaml
notification:
  mcp: {}
```

**Default:** `30`

**Result:** `get_mcp_timeout()` returns `30` (default used)

## Security: Secrets Enforcement

Secrets (API keys, passwords, tokens) **must** come from environment variables only. They are never read from YAML files, even if present.

**Secret Configuration Values:**
- `OPENAI_API_KEY`
- `PUSHOVER_USER_KEY`
- `GMAIL_RECIPIENT`

**Example:**

```python
# This will ONLY check environment variables
api_key = settings.get_openai_api_key()

# Even if settings.yaml contains:
# secrets:
#   openai_api_key: "sk-..."
# 
# The value will NOT be read from YAML (returns None if not in env)
```

## Available Configuration Accessors

### MCP Configuration
- `get_mcp_endpoint()` - MCP endpoint URL (supports HTTP/S for viaSocket)
- `get_mcp_timeout()` - Connection timeout in seconds
- `get_mcp_max_retries()` - Maximum connection retry attempts
- `get_mcp_retry_delay()` - Delay between retries in seconds
- `get_notification_channels()` - List of enabled notification channels

### Runtime Configuration
- `get_log_level()` - Logging level (INFO, DEBUG, ERROR, etc.)
- `get_enable_hooks()` - Whether hooks are enabled
- `get_save_output()` - Whether output should be saved

### Path Configuration
- `get_data_dir()` - Data directory path
- `get_output_log_path()` - Output log file path

### Secret Configuration
- `get_openai_api_key()` - OpenAI API key (env only)
- `get_pushover_user_key()` - Pushover user key (env only)
- `get_gmail_recipient()` - Gmail recipient email (env only)

## Usage

### Basic Usage

```python
from config.settings_loader import get_settings

# Get global settings instance
settings = get_settings()

# Access configuration values
endpoint = settings.get_mcp_endpoint()
timeout = settings.get_mcp_timeout()
log_level = settings.get_log_level()
```

### Custom Config Path

```python
from config.settings_loader import SettingsLoader

# Load from custom path
settings = SettingsLoader(config_path='/path/to/custom/settings.yaml')
```

### Testing

```python
from config.settings_loader import reset_settings

# Reset singleton for testing
reset_settings()
```

## Type Conversion

The SettingsLoader automatically converts string values to appropriate types:

- **Integers:** `"90"` → `90`
- **Booleans:** `"true"`, `"1"`, `"yes"`, `"on"` → `True`
- **Lists:** `"email,pushover,slack"` → `['email', 'pushover', 'slack']`

## Error Handling

The SettingsLoader raises `ConfigurationError` for:

1. **Invalid YAML:** Malformed YAML files
2. **Missing Required Settings:** When `required=True` and value not found
3. **Secret Not in Environment:** When secret is required but not in env vars

```python
from config.settings_loader import ConfigurationError

try:
    settings = SettingsLoader(config_path='invalid.yaml')
except ConfigurationError as e:
    print(f"Configuration error: {e}")
    print(f"Config key: {e.config_key}")
```

## viaSocket MCP Support

The SettingsLoader supports viaSocket MCP endpoints that use HTTP/HTTPS instead of WebSocket:

```python
# HTTP/HTTPS endpoints are accepted as-is
endpoint = settings.get_mcp_endpoint()
# Returns: "https://mcp.viasocket.com/6919df86112ef41ccccefee1-54132/sse"

# No protocol conversion or enforcement
# Endpoint is passed unchanged to MCPClient
```

## Testing

Comprehensive unit tests verify the priority system:

```bash
# Run all settings loader tests
python -m pytest tests/unit/test_settings_loader.py -v

# Run specific test
python -m pytest tests/unit/test_settings_loader.py::TestSettingsLoaderPriority::test_full_priority_chain -v
```

## Demonstration

Run the configuration priority demonstration:

```bash
python examples/config_priority_demo.py
```

This will display:
- Current configuration values
- Configuration sources (env, YAML, or default)
- Priority system explanation

## Best Practices

1. **Use environment variables for secrets** - Never put API keys in YAML
2. **Use YAML for environment-specific settings** - Different values per environment
3. **Use defaults for sensible fallbacks** - Safe values when nothing is configured
4. **Document required settings** - Make it clear what must be configured
5. **Validate early** - Check configuration at startup, not during execution

## Migration Guide

If you're migrating from direct environment variable or YAML reading:

**Before:**
```python
import os
import yaml

# Direct access (bad)
endpoint = os.getenv('MCP_ENDPOINT')
with open('config/settings.yaml') as f:
    config = yaml.safe_load(f)
    timeout = config['notification']['mcp']['timeout']
```

**After:**
```python
from config.settings_loader import get_settings

# Use SettingsLoader (good)
settings = get_settings()
endpoint = settings.get_mcp_endpoint()
timeout = settings.get_mcp_timeout()
```

## Summary

The configuration priority system provides:

✅ **Flexibility** - Override any setting via environment variables  
✅ **Security** - Secrets must come from environment only  
✅ **Simplicity** - Single source of truth for configuration  
✅ **Type Safety** - Automatic type conversion and validation  
✅ **Testability** - Easy to mock and test  
✅ **Documentation** - Clear accessor methods with type hints
