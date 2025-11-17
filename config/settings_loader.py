"""Settings loader for IncidentOps configuration.

Loads settings.yaml with environment variable interpolation.
Supports ${VAR_NAME} syntax for environment variable expansion.

All secrets must come from environment variables only.
"""

import os
import yaml
import re
from typing import Any, Optional, Dict
from pathlib import Path
from dotenv import load_dotenv


class ConfigurationError(Exception):
    """Exception raised when configuration is invalid or missing."""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        """Initialize configuration error.
        
        Args:
            message (str): Human-readable error message.
            config_key (str, optional): Configuration key that is invalid/missing.
        """
        super().__init__(message)
        self.config_key = config_key


class DotDict(dict):
    """Dictionary with dot-notation access to nested keys.
    
    Allows accessing nested dictionary values using dot notation:
    settings.notification.mcp.endpoint instead of settings['notification']['mcp']['endpoint']
    """
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize DotDict with nested conversion.
        
        Args:
            data (dict): Dictionary to convert to DotDict.
        """
        super().__init__()
        for key, value in data.items():
            if isinstance(value, dict):
                self[key] = DotDict(value)
            else:
                self[key] = value
    
    def __getattr__(self, key: str) -> Any:
        """Get attribute using dot notation.
        
        Args:
            key (str): Attribute name.
            
        Returns:
            Any: Value at the key.
            
        Raises:
            AttributeError: If key doesn't exist.
        """
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")
    
    def __setattr__(self, key: str, value: Any) -> None:
        """Set attribute using dot notation.
        
        Args:
            key (str): Attribute name.
            value (Any): Value to set.
        """
        self[key] = value
    
    def __delattr__(self, key: str) -> None:
        """Delete attribute using dot notation.
        
        Args:
            key (str): Attribute name.
        """
        try:
            del self[key]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{key}'")


class SettingsLoader(DotDict):
    """Simplified configuration loader with YAML environment interpolation.
    
    Loads settings.yaml and expands ${VAR_NAME} placeholders with environment variables.
    Provides dot-notation access: settings.notification.mcp.endpoint
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize settings loader.
        
        Args:
            config_path (str, optional): Path to settings.yaml file.
                Defaults to 'config/settings.yaml'.
        """
        # Load environment variables from .env file
        load_dotenv()
        
        # Determine config file path
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'settings.yaml'
            )
        
        self.config_path = config_path
        
        # Load YAML and expand environment variables
        config = self._load_yaml_with_env_expansion()
        
        # Initialize DotDict with config
        super().__init__(config)
        
        # Validate required settings
        self._validate_required_settings()
    
    def _convert_type(self, value: str, var_name: str = "") -> Any:
        """Convert string value to appropriate type.
        
        Args:
            value (str): String value to convert.
            var_name (str): Variable name for special handling.
            
        Returns:
            Any: Converted value (int, bool, list, or str).
        """
        # Special handling for comma-separated lists
        if var_name == 'NOTIFICATION_CHANNELS' and ',' in value:
            return [ch.strip() for ch in value.split(',') if ch.strip()]
        
        # Try boolean conversion
        if value.lower() in ('true', 'yes', 'on', '1'):
            return True
        if value.lower() in ('false', 'no', 'off', '0', ''):
            return False
        
        # Try integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _expand_env_vars(self, value: Any) -> Any:
        """Recursively expand ${VAR} placeholders in configuration values.
        
        Args:
            value (Any): Configuration value (can be str, dict, list, etc.)
            
        Returns:
            Any: Value with environment variables expanded.
        """
        if isinstance(value, str):
            # Check if entire value is a single placeholder
            single_placeholder = re.match(r'^\$\{([^}]+)\}$', value)
            if single_placeholder:
                var_name = single_placeholder.group(1)
                env_value = os.getenv(var_name)
                if env_value is not None:
                    # Convert type for single placeholder
                    return self._convert_type(env_value, var_name)
                # Return None for unset variables
                return None
            
            # Replace ${VAR_NAME} with environment variable value (for partial replacements)
            def replace_env_var(match):
                var_name = match.group(1)
                env_value = os.getenv(var_name)
                if env_value is None:
                    return ''  # Empty string for unset vars in partial replacements
                return env_value
            
            return re.sub(r'\$\{([^}]+)\}', replace_env_var, value)
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        else:
            return value
    
    def _load_yaml_with_env_expansion(self) -> Dict[str, Any]:
        """Load YAML configuration and expand environment variables.
        
        Returns:
            dict: Configuration with environment variables expanded.
            
        Raises:
            ConfigurationError: If YAML file cannot be loaded or parsed.
        """
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                # Return empty config if file doesn't exist (will rely on env vars)
                return {}
            
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Expand ${VAR} placeholders in the loaded config
            config = self._expand_env_vars(config)
            
            return config
            
        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Failed to parse YAML configuration from {self.config_path}: {str(e)}",
                config_key="yaml_file"
            )
        except ConfigurationError:
            # Re-raise ConfigurationError without wrapping
            raise
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from {self.config_path}: {str(e)}",
                config_key="yaml_file"
            )
    
    def _validate_required_settings(self) -> None:
        """Validate that required settings are present.
        
        Raises:
            ConfigurationError: If required settings are missing.
        """
        # Only validate if notification section exists
        # This allows for minimal test YAML files
        if 'notification' in self:
            if 'mcp' not in self.notification:
                raise ConfigurationError(
                    "Configuration structure is invalid: missing notification.mcp",
                    config_key="notification.mcp"
                )
            if 'endpoint' not in self.notification.mcp:
                raise ConfigurationError(
                    "Configuration structure is invalid: missing notification.mcp.endpoint",
                    config_key="notification.mcp.endpoint"
                )
    
    # Secret Accessor (must come from environment only)
    
    def get_secret(self, env_key: str) -> Optional[str]:
        """Get secret from environment variable only.
        
        Secrets must never be stored in YAML files.
        
        Args:
            env_key (str): Environment variable name.
            
        Returns:
            str: Secret value or None if not set.
            
        Example:
            api_key = settings.get_secret('OPENAI_API_KEY')
            pushover_key = settings.get_secret('PUSHOVER_USER_KEY')
        """
        return os.getenv(env_key)


# Global settings instance
_settings_instance: Optional[SettingsLoader] = None


def get_settings(config_path: Optional[str] = None) -> SettingsLoader:
    """Get global settings instance (singleton pattern).
    
    Args:
        config_path (str, optional): Path to settings.yaml file.
            Only used on first call.
    
    Returns:
        SettingsLoader: Global settings instance.
    """
    global _settings_instance
    
    if _settings_instance is None:
        _settings_instance = SettingsLoader(config_path)
    
    return _settings_instance


def reset_settings() -> None:
    """Reset global settings instance (useful for testing)."""
    global _settings_instance
    _settings_instance = None
