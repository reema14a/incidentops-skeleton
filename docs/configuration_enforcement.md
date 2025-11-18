# Configuration Access Enforcement

## Overview

This document describes the configuration access policy for the IncidentOps project. All configuration access must go through the centralized `config.settings_loader` module.

## Policy

### ✅ ALLOWED

- **Using `config.settings_loader`**: All agents, orchestrators, and application code must use the `get_settings()` function from `config.settings_loader` to access configuration.

```python
from config.settings_loader import get_settings

settings = get_settings()
api_key = settings.get_openai_api_key()
endpoint = settings.get_mcp_endpoint()
```

### ❌ PROHIBITED

The following patterns are **strictly prohibited** in all application code (agents, orchestrators, hooks, utilities):

1. **Direct environment variable access**:
   ```python
   # ❌ WRONG
   import os
   api_key = os.getenv('OPENAI_API_KEY')
   endpoint = os.environ['MCP_ENDPOINT']
   ```

2. **Direct YAML file reading**:
   ```python
   # ❌ WRONG
   import yaml
   with open('config/settings.yaml', 'r') as f:
       config = yaml.safe_load(f)
   ```

3. **Direct .env file loading**:
   ```python
   # ❌ WRONG
   from dotenv import load_dotenv
   load_dotenv()
   ```

### Exceptions

The following files are **exempt** from this policy:

1. **`config/settings_loader.py`**: This is the centralized configuration module and must access environment variables and YAML files directly.

2. **Test files for settings_loader** (`tests/unit/test_settings_loader.py`): These tests need to manipulate environment variables to test the settings loader behavior.

## Rationale

### Benefits of Centralized Configuration

1. **Single Source of Truth**: All configuration logic is in one place, making it easier to understand and maintain.

2. **Priority Management**: The settings loader enforces a clear priority order:
   - Environment variables (highest priority)
   - settings.yaml
   - Secure defaults (lowest priority)

3. **Security**: Secrets are enforced to come only from environment variables, never from YAML files.

4. **Validation**: Configuration values are validated and type-checked in one place.

5. **Testability**: Tests can easily mock or override configuration by using the `reset_settings()` function.

6. **Consistency**: All code uses the same configuration interface, reducing bugs and confusion.

## Configuration Priority

The settings loader implements the following priority order:

1. **Environment Variables** (highest priority)
   - Example: `MCP_ENDPOINT`, `OPENAI_API_KEY`, `LOG_LEVEL`
   - Always checked first
   - Required for all secrets

2. **settings.yaml**
   - Example: `notification.mcp.endpoint`, `runtime.log_level`
   - Used if environment variable is not set
   - Cannot contain secrets

3. **Secure Defaults** (lowest priority)
   - Example: `log_level='INFO'`, `mcp_timeout=30`
   - Used if neither environment variable nor YAML value is set

## Adding New Configuration

When adding new configuration options:

1. **Add accessor method to `SettingsLoader` class**:
   ```python
   def get_my_new_setting(self) -> str:
       """Get my new setting description.
       
       Returns:
           str: Setting value (default: 'default_value').
       """
       return self._get_setting(
           env_key='MY_NEW_SETTING',
           yaml_path=['section', 'my_new_setting'],
           default='default_value',
           required=False,
           secret=False  # Set to True if this is a secret
       )
   ```

2. **Update documentation** in this file and in `config/settings.yaml` comments.

3. **Add tests** in `tests/unit/test_settings_loader.py`.

4. **Use the new setting** in your code:
   ```python
   from config.settings_loader import get_settings
   
   settings = get_settings()
   my_value = settings.get_my_new_setting()
   ```

## Validation

A validation script is provided to check for violations of this policy:

```bash
python scripts/validate_config_access.py
```

This script will:
- Scan all Python files (except exempted ones)
- Report any direct environment variable access
- Report any direct YAML file reading
- Exit with error code if violations are found

## Migration Guide

If you find code that violates this policy:

1. **Identify the configuration being accessed**:
   ```python
   # Old code
   api_key = os.getenv('OPENAI_API_KEY')
   ```

2. **Check if accessor exists** in `config.settings_loader`:
   - If yes, use it: `settings.get_openai_api_key()`
   - If no, add a new accessor method (see "Adding New Configuration" above)

3. **Replace the direct access**:
   ```python
   # New code
   from config.settings_loader import get_settings
   
   settings = get_settings()
   api_key = settings.get_openai_api_key()
   ```

4. **Test your changes** to ensure configuration is loaded correctly.

## Current Status

✅ **All agents are compliant** - All agent files use `config.settings_loader` exclusively.

✅ **Orchestrator is compliant** - The orchestrator does not access configuration directly.

✅ **LLM client is compliant** - The OpenAI client uses `config.settings_loader`.

✅ **No violations detected** - A scan of the codebase found no violations of this policy.

## Enforcement

This policy is enforced through:

1. **Code reviews**: All pull requests must follow this policy.
2. **Validation script**: Run `python scripts/validate_config_access.py` in CI/CD.
3. **Documentation**: This document and steering files clearly state the policy.
4. **Testing**: Tests verify that configuration is loaded correctly through the settings loader.
