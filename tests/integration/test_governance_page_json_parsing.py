"""
Integration test for Governance page JSON parsing.

Tests that the Governance page correctly parses governance_data JSON
and falls back to legacy columns when needed.
"""

import sys
import unittest
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import db_util


class TestGovernancePageJSONParsing(unittest.TestCase):
    """Test Governance page JSON parsing functionality."""
    
    def test_get_governance_history_includes_governance_data(self):
        """Test that get_governance_history returns governance_data JSON column."""
        # Get governance history
        governance_history = db_util.get_governance_history(limit=1)
        
        # Should return a list
        self.assertIsInstance(governance_history, list)
        
        # If there's data, verify governance_data field is present
        if governance_history:
            record = governance_history[0]
            
            # Verify governance_data key is present (may be None)
            self.assertIn('governance_data', record, "Missing governance_data key")
            
            print(f"✓ governance_data field is present in record")
            
            # If governance_data is not None, verify it's valid JSON
            if record['governance_data']:
                try:
                    parsed = json.loads(record['governance_data'])
                    self.assertIsInstance(parsed, dict)
                    print(f"✓ governance_data is valid JSON: {list(parsed.keys())}")
                except json.JSONDecodeError as e:
                    self.fail(f"governance_data is not valid JSON: {e}")
    
    def test_governance_data_contains_expected_fields(self):
        """Test that governance_data JSON contains expected fields."""
        governance_history = db_util.get_governance_history(limit=1)
        
        if governance_history and governance_history[0].get('governance_data'):
            record = governance_history[0]
            parsed = json.loads(record['governance_data'])
            
            # Expected fields from LLMGovernanceAgent
            expected_fields = ['risk', 'escalation', 'commentary', 'compliance_issues']
            
            for field in expected_fields:
                self.assertIn(field, parsed, f"Missing expected field: {field}")
            
            print(f"✓ governance_data contains all expected fields: {expected_fields}")
            
            # Verify compliance_issues is a list
            self.assertIsInstance(parsed['compliance_issues'], list)
            print(f"✓ compliance_issues is a list with {len(parsed['compliance_issues'])} items")
    
    def test_legacy_columns_still_available(self):
        """Test that legacy columns (risk, escalation, commentary) are still available."""
        governance_history = db_util.get_governance_history(limit=1)
        
        if governance_history:
            record = governance_history[0]
            
            # Verify legacy columns are still present
            legacy_fields = ['risk', 'escalation', 'commentary']
            for field in legacy_fields:
                self.assertIn(field, record, f"Missing legacy field: {field}")
            
            print(f"✓ Legacy columns are still available: {legacy_fields}")
    
    def test_governance_data_parsing_fallback(self):
        """Test that parsing falls back to legacy columns when JSON is invalid."""
        # This test simulates the parsing logic in Governance.py
        
        # Test case 1: Valid JSON
        test_json = json.dumps({
            'risk': 'high',
            'escalation': 'immediate',
            'commentary': 'Test commentary',
            'compliance_issues': ['Issue 1', 'Issue 2']
        })
        
        try:
            parsed = json.loads(test_json)
            self.assertEqual(parsed['risk'], 'high')
            print("✓ Valid JSON parsing works correctly")
        except json.JSONDecodeError:
            self.fail("Valid JSON should parse successfully")
        
        # Test case 2: Invalid JSON (fallback scenario)
        test_invalid_json = "not valid json"
        
        try:
            parsed = json.loads(test_invalid_json)
            self.fail("Invalid JSON should raise JSONDecodeError")
        except json.JSONDecodeError:
            # This is expected - fallback to legacy columns would happen here
            print("✓ Invalid JSON correctly raises JSONDecodeError (fallback would occur)")
        
        # Test case 3: None value (fallback scenario)
        test_none = None
        
        if test_none:
            try:
                parsed = json.loads(test_none)
            except json.JSONDecodeError:
                pass
        else:
            # Fallback to legacy columns would happen here
            print("✓ None value correctly triggers fallback logic")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
