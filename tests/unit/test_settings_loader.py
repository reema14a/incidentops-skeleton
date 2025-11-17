"""Unit tests for SettingsLoader configuration priority."""

import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch
from config.settings_loader import SettingsLoader, ConfigurationError, reset_settings


class TestSettingsLoaderPriority:
    """Test configuration loading priority: env vars > yaml > defaults."""
    
    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
        # Store original env vars to restore later
        self.original_env = {}
    
    def teardown_method(self):
        """Clean up environment variables after each test."""
        # Restore original environment
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_settings()
    
    def _backup_and_clear_env(self, *keys):
        """Backup and clear specified environment variables."""
        for key in keys:
            self.original_env[key] = os.getenv(key)
            os.environ.pop(key, None)
    
    def test_priority_env_over_yaml(self):
        """Test that environment variables are interpolated via ${VAR} syntax."""
        # Create temporary YAML config with ${VAR} syntax
        yaml_content = """
runtime:
  log_level: ${LOG_LEVEL}
notification:
  mcp:
    endpoint: ${MCP_ENDPOINT}
    timeout: ${MCP_TIMEOUT}
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            # Set environment variable
            self._backup_and_clear_env('LOG_LEVEL', 'MCP_ENDPOINT', 'MCP_TIMEOUT')
            os.environ['LOG_LEVEL'] = 'DEBUG'
            os.environ['MCP_ENDPOINT'] = 'env-endpoint'
            os.environ['MCP_TIMEOUT'] = '90'
            
            # Load settings
            loader = SettingsLoader(config_path=yaml_path)
            
            # Environment variables should be interpolated
            assert loader.runtime.log_level == 'DEBUG'
            assert loader.notification.mcp.endpoint == 'env-endpoint'
            assert loader.notification.mcp.timeout == 90
        finally:
            Path(yaml_path).unlink()
    
    def test_priority_yaml_over_defaults(self):
        """Test that YAML values take priority over defaults."""
        # Create temporary YAML config
        yaml_content = """
runtime:
  log_level: ERROR
notification:
  mcp:
    endpoint: test-endpoint
    timeout: 45
    max_retries: 5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            # Clear environment variables that might be loaded from .env
            self._backup_and_clear_env('LOG_LEVEL', 'MCP_TIMEOUT', 'MCP_MAX_RETRIES')
            
            # Reload settings after clearing env vars
            reset_settings()
            
            # Mock load_dotenv to prevent loading .env file
            with patch('config.settings_loader.load_dotenv'):
                loader = SettingsLoader(config_path=yaml_path)
            
            # YAML values should be used
            assert loader.runtime.log_level == 'ERROR'
            assert loader.notification.mcp.timeout == 45
            assert loader.notification.mcp.max_retries == 5
        finally:
            Path(yaml_path).unlink()
    
    def test_priority_defaults_when_nothing_set(self):
        """Test that YAML values are used when env vars are not set."""
        # Create YAML config with values
        yaml_content = """
runtime:
  log_level: INFO
notification:
  mcp:
    endpoint: test-endpoint
    timeout: 30
    max_retries: 3
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            # Clear environment variables
            self._backup_and_clear_env('LOG_LEVEL', 'MCP_TIMEOUT', 'MCP_MAX_RETRIES')
            
            # Load settings
            loader = SettingsLoader(config_path=yaml_path)
            
            # YAML values should be used
            assert loader.runtime.log_level == 'INFO'
            assert loader.notification.mcp.timeout == 30
            assert loader.notification.mcp.max_retries == 3
        finally:
            Path(yaml_path).unlink()
    
    def test_full_priority_chain(self):
        """Test ${VAR} interpolation with mix of set and unset variables."""
        # Create YAML with ${VAR} syntax - some will be set, some won't
        yaml_content = """
runtime:
  log_level: ${LOG_LEVEL}
  enable_hooks: false
notification:
  mcp:
    endpoint: yaml-endpoint
    timeout: 50
    max_retries: 5
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            # Set only one environment variable
            self._backup_and_clear_env('LOG_LEVEL', 'MCP_TIMEOUT', 'MCP_MAX_RETRIES')
            os.environ['LOG_LEVEL'] = 'CRITICAL'
            
            # Load settings
            loader = SettingsLoader(config_path=yaml_path)
            
            # Verify:
            # 1. LOG_LEVEL from env (via ${VAR} interpolation)
            assert loader.runtime.log_level == 'CRITICAL'
            
            # 2. MCP_TIMEOUT from YAML (literal value, no ${VAR})
            assert loader.notification.mcp.timeout == 50
            
            # 3. MCP_MAX_RETRIES from YAML (literal value, no ${VAR})
            assert loader.notification.mcp.max_retries == 5
            
            # 4. ENABLE_HOOKS from YAML (literal value)
            assert loader.runtime.enable_hooks is False
        finally:
            Path(yaml_path).unlink()


class TestSecretHandling:
    """Test that secrets must come from environment variables only."""
    
    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
        self.original_env = {}
    
    def teardown_method(self):
        """Clean up after each test."""
        for key, value in self.original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        reset_settings()
    
    def test_secret_from_environment(self):
        """Test that secrets can be loaded from environment."""
        self.original_env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
        os.environ['OPENAI_API_KEY'] = 'test-api-key'
        
        loader = SettingsLoader()
        assert loader.get_secret('OPENAI_API_KEY') == 'test-api-key'
    
    def test_secret_not_in_yaml(self):
        """Test that secrets are not read from YAML even if present."""
        # Create YAML with secret (should be ignored)
        yaml_content = """
secrets:
  openai_api_key: "yaml-secret-key"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            self.original_env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY')
            os.environ.pop('OPENAI_API_KEY', None)
            
            # Reset settings after clearing env var
            reset_settings()
            
            # Mock load_dotenv to prevent loading .env file
            with patch('config.settings_loader.load_dotenv'):
                loader = SettingsLoader(config_path=yaml_path)
            
            # Secret should not be loaded from YAML
            assert loader.get_secret('OPENAI_API_KEY') is None
        finally:
            Path(yaml_path).unlink()


class TestMCPConfiguration:
    """Test MCP-specific configuration accessors."""
    
    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_mcp_endpoint_viasocket_http(self):
        """Test that viaSocket HTTP/S endpoints are accepted as-is."""
        yaml_content = """
notification:
  mcp:
    endpoint: "https://mcp.viasocket.com/test/sse"
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            # Clear MCP_ENDPOINT from environment
            original_endpoint = os.getenv('MCP_ENDPOINT')
            os.environ.pop('MCP_ENDPOINT', None)
            reset_settings()
            
            # Mock load_dotenv to prevent loading .env file
            with patch('config.settings_loader.load_dotenv'):
                loader = SettingsLoader(config_path=yaml_path)
            
            endpoint = loader.notification.mcp.endpoint
            
            # Should return HTTP endpoint unchanged
            assert endpoint == "https://mcp.viasocket.com/test/sse"
            assert endpoint.startswith('https://')
            
            # Restore original
            if original_endpoint:
                os.environ['MCP_ENDPOINT'] = original_endpoint
        finally:
            Path(yaml_path).unlink()
    
    def test_notification_channels_from_string(self):
        """Test parsing notification channels from comma-separated string."""
        original_env = os.getenv('NOTIFICATION_CHANNELS')
        try:
            os.environ['NOTIFICATION_CHANNELS'] = 'email,pushover,slack'
            
            loader = SettingsLoader()
            channels = loader.notification.channels
            
            assert channels == ['email', 'pushover', 'slack']
        finally:
            if original_env is None:
                os.environ.pop('NOTIFICATION_CHANNELS', None)
            else:
                os.environ['NOTIFICATION_CHANNELS'] = original_env
    
    def test_notification_channels_from_list(self):
        """Test notification channels from YAML list."""
        yaml_content = """
notification:
  mcp:
    endpoint: test-endpoint
  channels:
    - email
    - pushover
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            loader = SettingsLoader(config_path=yaml_path)
            channels = loader.notification.channels
            
            assert channels == ['email', 'pushover']
        finally:
            Path(yaml_path).unlink()


class TestConfigurationValidation:
    """Test configuration validation and error handling."""
    
    def setup_method(self):
        """Reset settings before each test."""
        reset_settings()
    
    def teardown_method(self):
        """Clean up after each test."""
        reset_settings()
    
    def test_invalid_yaml_raises_error(self):
        """Test that invalid YAML raises ConfigurationError."""
        yaml_content = """
invalid: yaml: content:
  - broken
"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                SettingsLoader(config_path=yaml_path)
            
            assert 'Failed to' in str(exc_info.value) and 'configuration' in str(exc_info.value).lower()
        finally:
            Path(yaml_path).unlink()
    
    def test_missing_yaml_uses_defaults(self):
        """Test that missing YAML file returns empty config (relies on env vars)."""
        # With no YAML file and no env vars, config will be empty
        # This is expected - configuration should come from YAML or env vars
        loader = SettingsLoader(config_path='/nonexistent/path/settings.yaml')
        
        # Config should be empty dict (no defaults)
        assert isinstance(loader, dict)
        # Should not have runtime section if not in YAML or env
        assert 'runtime' not in loader or loader.get('runtime') is None
    
    def test_type_conversion_for_integers(self):
        """Test that string values are converted to integers."""
        original_timeout = os.getenv('MCP_TIMEOUT')
        try:
            os.environ['MCP_TIMEOUT'] = '120'
            
            loader = SettingsLoader()
            timeout = loader.notification.mcp.timeout
            
            assert isinstance(timeout, int)
            assert timeout == 120
        finally:
            if original_timeout is None:
                os.environ.pop('MCP_TIMEOUT', None)
            else:
                os.environ['MCP_TIMEOUT'] = original_timeout
    
    def test_type_conversion_for_booleans(self):
        """Test that string values are converted to booleans."""
        original_hooks = os.getenv('ENABLE_HOOKS')
        try:
            os.environ['ENABLE_HOOKS'] = 'false'
            
            loader = SettingsLoader()
            enabled = loader.runtime.enable_hooks
            
            assert isinstance(enabled, bool)
            assert enabled is False
        finally:
            if original_hooks is None:
                os.environ.pop('ENABLE_HOOKS', None)
            else:
                os.environ['ENABLE_HOOKS'] = original_hooks
