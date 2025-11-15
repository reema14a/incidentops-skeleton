#!/usr/bin/env python3
"""Test to verify MonitorAgent implementation."""

from agents.monitor_agent import MonitorAgent

def test_monitor_agent():
    """Test the MonitorAgent with sample log file."""
    
    print("\n" + "="*60)
    print("MONITOR AGENT TEST")
    print("="*60)
    
    # Step 1: Run MonitorAgent to scan logs
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    # Step 2: Display detected alerts
    print("\n" + "="*60)
    print("DETECTED ALERTS:")
    print("="*60)
    
    if not alerts:
        print("  No alerts detected.")
    else:
        for i, alert in enumerate(alerts, 1):
            print(f"\nAlert #{i}:")
            print(f"  Timestamp: {alert['timestamp']}")
            print(f"  Level: {alert['level']}")
            print(f"  Message: {alert['message']}")
            print(f"  Line Number: {alert['line_number']}")
            print(f"  Raw Log: {alert['raw_log']}")
    
    # Step 3: Verify alert structure
    print("\n" + "="*60)
    print("VALIDATION:")
    print("="*60)
    
    # Verify all alerts have required fields
    required_fields = ['timestamp', 'level', 'message', 'line_number', 'raw_log']
    for field in required_fields:
        assert all(field in alert for alert in alerts), f"Missing {field} field in alerts"
        print(f"  ✓ All alerts have '{field}' field")
    
    # Verify alert levels are valid
    valid_levels = ['ERROR', 'WARNING']
    for alert in alerts:
        assert alert['level'] in valid_levels, f"Invalid level: {alert['level']}"
    print(f"  ✓ All alert levels are valid ({', '.join(valid_levels)})")
    
    # Verify we have some alerts (assuming sample_logs.txt has errors)
    assert len(alerts) > 0, "No alerts detected from sample logs"
    print(f"  ✓ Detected {len(alerts)} alert(s)")
    
    # Count by level
    error_count = sum(1 for a in alerts if a['level'] == 'ERROR')
    warning_count = sum(1 for a in alerts if a['level'] == 'WARNING')
    print(f"  ✓ ERROR alerts: {error_count}")
    print(f"  ✓ WARNING alerts: {warning_count}")
    
    print("\n" + "="*60)
    print("✓ MonitorAgent test passed successfully")
    print("="*60)
    
    return alerts

def test_monitor_agent_with_missing_file():
    """Test MonitorAgent behavior when log file is missing."""
    
    print("\n" + "="*60)
    print("MONITOR AGENT TEST - MISSING FILE")
    print("="*60)
    
    # Create MonitorAgent with non-existent log path
    monitor = MonitorAgent("Monitor", log_path="data/nonexistent.txt")
    alerts = monitor.run()
    
    # Should return empty list without crashing
    assert isinstance(alerts, list), "Should return a list"
    assert len(alerts) == 0, "Should return empty list for missing file"
    
    print("  ✓ Handles missing log file gracefully")
    print("  ✓ Returns empty alert list")
    
    print("\n" + "="*60)
    print("✓ Missing file test passed")
    print("="*60)
    
    return alerts

def test_monitor_agent_alert_parsing():
    """Test MonitorAgent alert parsing logic."""
    
    print("\n" + "="*60)
    print("MONITOR AGENT TEST - ALERT PARSING")
    print("="*60)
    
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    # Verify each alert has proper message extraction
    for alert in alerts:
        assert len(alert['message']) > 0, "Alert message should not be empty"
        assert alert['line_number'] > 0, "Line number should be positive"
        
        # Verify timestamp format (basic check)
        timestamp = alert['timestamp']
        assert len(timestamp) > 0, "Timestamp should not be empty"
        
        # Verify raw_log contains the level
        assert alert['level'] in alert['raw_log'], "Raw log should contain the alert level"
    
    print(f"  ✓ All {len(alerts)} alerts properly parsed")
    print("  ✓ Messages extracted correctly")
    print("  ✓ Timestamps present")
    print("  ✓ Line numbers tracked")
    print("  ✓ Raw logs preserved")
    
    print("\n" + "="*60)
    print("✓ Alert parsing test passed")
    print("="*60)

if __name__ == "__main__":
    # Run all tests
    test_monitor_agent()
    test_monitor_agent_with_missing_file()
    test_monitor_agent_alert_parsing()
    
    print("\n" + "="*60)
    print("ALL MONITOR AGENT TESTS PASSED ✓")
    print("="*60)
