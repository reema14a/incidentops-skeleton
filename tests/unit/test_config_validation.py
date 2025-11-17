"""Tests for configuration access validation script."""

import unittest
import tempfile
import shutil
from pathlib import Path
import sys

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'scripts'))

from validate_config_access import scan_file, is_exempt, VIOLATION_PATTERNS


class TestConfigValidation(unittest.TestCase):
    """Test configuration access validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_is_exempt_settings_loader(self):
        """Test that settings_loader.py is exempt."""
        self.assertTrue(is_exempt('config/settings_loader.py'))
    
    def test_is_exempt_test_file(self):
        """Test that test_settings_loader.py is exempt."""
        self.assertTrue(is_exempt('tests/unit/test_settings_loader.py'))
    
    def test_is_not_exempt_agent(self):
        """Test that agent files are not exempt."""
        self.assertFalse(is_exempt('agents/monitor_agent.py'))
        self.assertFalse(is_exempt('agents/llm_alert_summary_agent.py'))
    
    def test_scan_file_detects_os_getenv(self):
        """Test detection of os.getenv() usage."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
import os

def get_config():
    api_key = os.getenv('API_KEY')
    return api_key
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 1)
        self.assertIn('os.getenv()', violations[0][1])
    
    def test_scan_file_detects_os_environ(self):
        """Test detection of os.environ[] usage."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
import os

def get_config():
    api_key = os.environ['API_KEY']
    return api_key
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 1)
        self.assertIn('os.environ[]', violations[0][1])
    
    def test_scan_file_detects_yaml_load(self):
        """Test detection of yaml.load() usage."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
import yaml

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.load(f)
    return config
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 1)
        self.assertIn('yaml.load()', violations[0][1])
    
    def test_scan_file_detects_yaml_safe_load(self):
        """Test detection of yaml.safe_load() usage."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
import yaml

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    return config
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 1)
        self.assertIn('yaml.safe_load()', violations[0][1])
    
    def test_scan_file_detects_load_dotenv(self):
        """Test detection of load_dotenv() usage."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
from dotenv import load_dotenv

load_dotenv()
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 1)
        self.assertIn('load_dotenv()', violations[0][1])
    
    def test_scan_file_ignores_comments(self):
        """Test that comments are ignored."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
# This is a comment about os.getenv()
# api_key = os.getenv('API_KEY')

def get_config():
    # Don't use os.getenv() directly
    from config.settings_loader import get_settings
    settings = get_settings()
    return settings.get_openai_api_key()
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 0)
    
    def test_scan_file_detects_multiple_violations(self):
        """Test detection of multiple violations in one file."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
import os
import yaml

def bad_config():
    api_key = os.getenv('API_KEY')
    endpoint = os.environ['ENDPOINT']
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    return api_key, endpoint, config
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 3)
    
    def test_scan_file_accepts_settings_loader(self):
        """Test that using settings_loader is not flagged."""
        test_file = self.temp_path / 'test.py'
        test_file.write_text("""
from config.settings_loader import get_settings

def get_config():
    settings = get_settings()
    api_key = settings.get_openai_api_key()
    endpoint = settings.get_mcp_endpoint()
    return api_key, endpoint
""")
        
        violations = scan_file(test_file)
        self.assertEqual(len(violations), 0)
    
    def test_violation_patterns_complete(self):
        """Test that all expected patterns are defined."""
        pattern_types = [pattern[1] for pattern in VIOLATION_PATTERNS]
        
        self.assertIn('Direct environment variable access using os.getenv()', pattern_types)
        self.assertIn('Direct environment variable access using os.environ[]', pattern_types)
        self.assertIn('Direct YAML file reading using yaml.load()', pattern_types)
        self.assertIn('Direct YAML file reading using yaml.safe_load()', pattern_types)
        self.assertIn('Direct .env file loading using load_dotenv()', pattern_types)


if __name__ == '__main__':
    unittest.main()
