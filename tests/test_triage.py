#!/usr/bin/env python3
"""Quick test to verify TriageAgent implementation."""

from agents.monitor_agent import MonitorAgent
from agents.triage_agent import TriageAgent

def test_triage_agent():
    """Test the TriageAgent with real MonitorAgent output."""
    
    # Step 1: Run MonitorAgent to get alerts
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    print("\n" + "="*60)
    print("MONITOR OUTPUT:")
    print("="*60)
    for alert in alerts:
        print(f"  {alert['timestamp']} [{alert['level']}] {alert['message']}")
    
    # Step 2: Run TriageAgent to classify alerts
    print("\n" + "="*60)
    print("TRIAGE PROCESSING:")
    print("="*60)
    triage = TriageAgent("Triage")
    triaged_alerts = triage.run(alerts)
    
    # Step 3: Display triaged results
    print("\n" + "="*60)
    print("TRIAGED RESULTS:")
    print("="*60)
    for alert in triaged_alerts:
        print(f"  [{alert['severity'].upper()}] [{alert['category'].upper()}]")
        print(f"    Message: {alert['message']}")
        print(f"    Original Level: {alert['level']}")
        print()
    
    # Verify all alerts have severity and category
    assert all('severity' in a for a in triaged_alerts), "Missing severity field"
    assert all('category' in a for a in triaged_alerts), "Missing category field"
    
    print("✓ All alerts successfully triaged with severity and category")
    return triaged_alerts

if __name__ == "__main__":
    test_triage_agent()
