#!/usr/bin/env python3
"""Test to verify ResolutionAgent implementation."""

from agents.monitor_agent import MonitorAgent
from agents.triage_agent import TriageAgent
from agents.resolution_agent import ResolutionAgent

def test_resolution_agent():
    """Test the ResolutionAgent with real TriageAgent output."""
    
    # Step 1: Run MonitorAgent to get alerts
    monitor = MonitorAgent("Monitor")
    alerts = monitor.run()
    
    # Step 2: Run TriageAgent to classify alerts
    triage = TriageAgent("Triage")
    triaged_alerts = triage.run(alerts)
    
    print("\n" + "="*60)
    print("TRIAGED ALERTS INPUT:")
    print("="*60)
    for alert in triaged_alerts:
        print(f"  [{alert['severity'].upper()}] [{alert['category'].upper()}] {alert['message']}")
    
    # Step 3: Run ResolutionAgent to generate remediation plans
    print("\n" + "="*60)
    print("RESOLUTION PROCESSING:")
    print("="*60)
    resolution = ResolutionAgent("Resolution")
    resolution_plans = resolution.run(triaged_alerts)
    
    # Step 4: Display resolution plans
    print("\n" + "="*60)
    print("RESOLUTION PLANS:")
    print("="*60)
    for plan in resolution_plans:
        print(f"\nAlert ID: {plan['alert_id']}")
        print(f"  Severity: {plan['severity'].upper()}")
        print(f"  Category: {plan['category'].upper()}")
        print(f"  Priority: {plan['priority']}")
        print(f"  Message: {plan['message']}")
        print(f"  Reasoning: {plan['reasoning']}")
        print(f"  Recommended Actions:")
        for i, action in enumerate(plan['recommended_actions'], 1):
            print(f"    {i}. {action}")
    
    # Verify all plans have required fields
    assert len(resolution_plans) == len(triaged_alerts), "Plan count mismatch"
    assert all('alert_id' in p for p in resolution_plans), "Missing alert_id field"
    assert all('severity' in p for p in resolution_plans), "Missing severity field"
    assert all('category' in p for p in resolution_plans), "Missing category field"
    assert all('recommended_actions' in p for p in resolution_plans), "Missing recommended_actions field"
    assert all('priority' in p for p in resolution_plans), "Missing priority field"
    assert all('reasoning' in p for p in resolution_plans), "Missing reasoning field"
    assert all(len(p['recommended_actions']) > 0 for p in resolution_plans), "Empty action lists"
    
    print("\n" + "="*60)
    print("✓ All resolution plans successfully generated")
    print(f"✓ Total plans: {len(resolution_plans)}")
    print(f"✓ All required fields present")
    print("="*60)
    
    return resolution_plans

if __name__ == "__main__":
    test_resolution_agent()
