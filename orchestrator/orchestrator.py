from agents.monitor_agent import MonitorAgent
from agents.triage_agent import TriageAgent
from agents.resolution_agent import ResolutionAgent
from agents.opslog_agent import OpsLogAgent

def run_pipeline():
    monitor = MonitorAgent("MonitorAgent")
    triage = TriageAgent("TriageAgent")
    resolution = ResolutionAgent("ResolutionAgent")
    opslog = OpsLogAgent("OpsLogAgent")

    alerts = monitor.run()
    triaged = triage.run(alerts)
    plans = resolution.run(triaged)
    summary = opslog.run(plans)

    print(f"\n✅ Pipeline complete: {summary}")
