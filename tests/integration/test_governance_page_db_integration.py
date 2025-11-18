"""
Integration test for Governance page database integration.

Tests that the Governance page correctly reads historical governance data
from the database using get_governance_history().
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from db import db_util


class TestGovernancePageDBIntegration(unittest.TestCase):
    """Test Governance page database integration."""
    
    def test_get_governance_history_returns_data(self):
        """Test that get_governance_history returns data from the database."""
        # Get all governance history
        governance_history = db_util.get_governance_history()
        
        # Should return a list
        self.assertIsInstance(governance_history, list)
        
        # If there's data, verify structure
        if governance_history:
            record = governance_history[0]
            
            # Verify required keys are present
            required_keys = ['id', 'run_id', 'timestamp', 'risk', 'escalation', 'commentary']
            for key in required_keys:
                self.assertIn(key, record, f"Missing key: {key}")
            
            # Verify data types
            self.assertIsInstance(record['id'], int)
            self.assertIsInstance(record['run_id'], int)
            self.assertIsInstance(record['timestamp'], str)
            
            print(f"✓ Retrieved {len(governance_history)} governance records")
            print(f"✓ Sample record structure: {list(record.keys())}")
    
    def test_get_governance_history_with_limit(self):
        """Test that get_governance_history respects the limit parameter."""
        # Get limited governance history
        limited_history = db_util.get_governance_history(limit=5)
        
        # Should return a list
        self.assertIsInstance(limited_history, list)
        
        # Should not exceed the limit
        self.assertLessEqual(len(limited_history), 5)
        
        print(f"✓ get_governance_history(limit=5) returned {len(limited_history)} records")
    
    def test_get_governance_history_ordered_by_timestamp(self):
        """Test that governance history is ordered by timestamp descending."""
        governance_history = db_util.get_governance_history()
        
        if len(governance_history) >= 2:
            # Verify records are ordered by timestamp descending (most recent first)
            for i in range(len(governance_history) - 1):
                current_timestamp = governance_history[i]['timestamp']
                next_timestamp = governance_history[i + 1]['timestamp']
                
                # Current should be >= next (descending order)
                self.assertGreaterEqual(
                    current_timestamp, 
                    next_timestamp,
                    "Records should be ordered by timestamp descending"
                )
            
            print(f"✓ Records are correctly ordered by timestamp descending")
    
    def test_compliance_issues_for_governance_runs(self):
        """Test that compliance issues can be retrieved for governance runs."""
        governance_history = db_util.get_governance_history(limit=1)
        
        if governance_history:
            run_id = governance_history[0]['run_id']
            
            # Query compliance issues for this run
            with db_util.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT issue
                    FROM compliance_issues
                    WHERE run_id = ?
                    ORDER BY id ASC
                """, (run_id,))
                rows = cursor.fetchall()
                compliance_issues = [row['issue'] for row in rows]
            
            # Should return a list (may be empty)
            self.assertIsInstance(compliance_issues, list)
            
            print(f"✓ Retrieved {len(compliance_issues)} compliance issues for run_id {run_id}")
    
    def test_risk_level_distribution(self):
        """Test that risk level distribution can be calculated from governance history."""
        governance_history = db_util.get_governance_history()
        
        # Calculate risk counts
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0, 'unknown': 0}
        
        for record in governance_history:
            risk = record.get('risk', 'unknown')
            if risk:
                risk = risk.lower()
                if risk in risk_counts:
                    risk_counts[risk] += 1
                else:
                    risk_counts['unknown'] += 1
        
        # Verify we can calculate distribution
        total_records = len(governance_history)
        total_counted = sum(risk_counts.values())
        
        self.assertEqual(
            total_records, 
            total_counted,
            "All records should be counted in risk distribution"
        )
        
        print(f"✓ Risk distribution: {risk_counts}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
