"""
Unit tests for Governance page layout redesign.

Tests verify the new layout structure with Summary Card, Overview tab, and Historical tab.
"""

import sys
from pathlib import Path

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_governance_page_imports():
    """Test that the Governance page can be imported without errors."""
    try:
        # Import the page module
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "governance_page",
            ROOT / "ui" / "pages" / "Governance.py"
        )
        governance_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(governance_module)
        
        # Verify key functions exist
        assert hasattr(governance_module, 'get_latest_governance_data')
        assert hasattr(governance_module, 'get_risk_emoji')
        assert hasattr(governance_module, 'format_timestamp')
        assert hasattr(governance_module, "render_page")

        print("✓ Governance page imports successfully")
        print("✓ All required functions are present")
        
    except Exception as e:
        raise AssertionError(f"Failed to import Governance page: {str(e)}")


def test_helper_functions():
    """Test helper functions used in the Governance page."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "governance_page",
        ROOT / "ui" / "pages" / "Governance.py"
    )
    governance_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(governance_module)
    
    # Test get_risk_emoji
    assert governance_module.get_risk_emoji('critical') == '🔴'
    assert governance_module.get_risk_emoji('high') == '🟠'
    assert governance_module.get_risk_emoji('medium') == '🟡'
    assert governance_module.get_risk_emoji('low') == '🟢'
    
    # Test format_timestamp
    assert governance_module.format_timestamp('N/A') == 'N/A'
    assert governance_module.format_timestamp('') == 'N/A'
    
    print("✓ All helper functions work correctly")


def test_governance_page_structure():
    """Test that the Governance page has the expected structure."""
    governance_file = ROOT / "ui" / "pages" / "Governance.py"
    content = governance_file.read_text()
    
    # Verify Summary Card section exists
    assert "# SUMMARY CARD" in content or "Summary Card" in content
    assert 'st.subheader("📊 Summary Card")' in content
    
    # Verify tabbed interface exists
    assert 'st.tabs([' in content
    assert '"📋 Overview"' in content
    assert '"📈 Historical"' in content
    
    # Verify Overview tab content
    assert 'with overview_tab:' in content
    assert 'st.subheader("🎯 Risk Assessment")' in content
    assert 'st.subheader("📢 Escalation Decision")' in content
    assert 'st.subheader("📋 Compliance Analysis")' in content
    assert 'st.subheader("💬 Governance Commentary")' in content
    
    # Verify Historical tab content
    assert 'with historical_tab:' in content
    assert 'st.subheader("📈 Governance Analytics")' in content
    assert 'st.subheader("🔍 Key Observations")' in content
    assert 'st.subheader("📊 Trend Analysis")' in content
    assert 'st.subheader("📜 Governance History")' in content
    assert 'st.subheader("🔍 Detailed Run Analysis")' in content
    
    # Verify collapsible history (expanders for each run)
    assert 'with st.expander(' in content
    assert 'expanded=False' in content
    
    print("✓ Governance page has correct structure")
    print("✓ Summary Card section present")
    print("✓ Overview tab with all required sections")
    print("✓ Historical tab with analytics and collapsible history")


if __name__ == "__main__":
    test_governance_page_imports()
    test_helper_functions()
    test_governance_page_structure()
    print("\n✅ All Governance page layout tests passed!")
