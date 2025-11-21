"""
Integration test for Deep Governance Insights page trend charts.

This test verifies that the DB-backed trend charts can be rendered
correctly when database data is available.
"""

import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.pages.Deep_Governance_Insights import (
    get_risk_trend,
    get_compliance_trend,
    get_escalation_text_counts,
    get_risk_emoji
)


def test_get_risk_trend():
    """Test that get_risk_trend returns a list."""
    result = get_risk_trend()
    assert isinstance(result, list), "get_risk_trend should return a list"


def test_get_compliance_trend():
    """Test that get_compliance_trend returns a list."""
    result = get_compliance_trend()
    assert isinstance(result, list), "get_compliance_trend should return a list"


def test_get_escalation_text_counts():
    """Test that get_escalation_text_counts returns a dict."""
    result = get_escalation_text_counts()
    assert isinstance(result, dict), "get_escalation_text_counts should return a dict"


def test_get_risk_emoji():
    """Test that get_risk_emoji returns correct emojis for risk levels."""
    assert get_risk_emoji('low') == '🟢', "Low risk should return green emoji"
    assert get_risk_emoji('medium') == '🟡', "Medium risk should return yellow emoji"
    assert get_risk_emoji('high') == '🟠', "High risk should return orange emoji"
    assert get_risk_emoji('critical') == '🔴', "Critical risk should return red emoji"
    
    # Test case insensitivity
    assert get_risk_emoji('LOW') == '🟢', "Should handle uppercase"
    assert get_risk_emoji('CRITICAL') == '🔴', "Should handle uppercase"


def test_risk_trend_data_structure():
    """Test that risk trend data has the expected structure when data exists."""
    result = get_risk_trend()
    
    if result:  # Only test structure if data exists
        for record in result:
            assert 'run_id' in record, "Risk trend record should have run_id"
            assert 'timestamp' in record, "Risk trend record should have timestamp"
            assert 'risk' in record, "Risk trend record should have risk"
            assert 'date' in record, "Risk trend record should have date"
            assert 'time' in record, "Risk trend record should have time"


def test_compliance_trend_data_structure():
    """Test that compliance trend data has the expected structure when data exists."""
    result = get_compliance_trend()
    
    if result:  # Only test structure if data exists
        for record in result:
            assert 'run_id' in record, "Compliance trend record should have run_id"
            assert 'timestamp' in record, "Compliance trend record should have timestamp"
            assert 'issue_count' in record, "Compliance trend record should have issue_count"
            assert 'date' in record, "Compliance trend record should have date"
            assert 'time' in record, "Compliance trend record should have time"


def test_escalation_counts_data_structure():
    """Test that escalation counts data has the expected structure when data exists."""
    result = get_escalation_text_counts()
    
    if result:  # Only test structure if data exists
        for escalation_text, count in result.items():
            assert isinstance(escalation_text, str), "Escalation text should be a string"
            assert isinstance(count, int), "Count should be an integer"
            assert count > 0, "Count should be positive"


if __name__ == "__main__":
    # Run tests
    test_get_risk_trend()
    test_get_compliance_trend()
    test_get_escalation_text_counts()
    test_get_risk_emoji()
    test_risk_trend_data_structure()
    test_compliance_trend_data_structure()
    test_escalation_counts_data_structure()
    
    print("✓ All tests passed!")
