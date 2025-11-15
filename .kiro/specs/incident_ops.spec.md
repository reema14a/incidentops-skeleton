---
name: "IncidentOps AIOps Pipeline"
status: "draft"
description: "Specification for the multi-agent IncidentOps system supporting log monitoring, incident classification, resolution suggestion, and audit logging."
---

# Overview
IncidentOps is a sequential multi-agent pipeline for AIOps-style incident handling.  
The system reads logs, identifies anomalies, classifies severity, suggests potential remediations, and logs all actions for audit and governance.

The pipeline stages:
1. **MonitorAgent** – Detect anomalies in log or metric data.
2. **TriageAgent** – Classify severity and incident category.
3. **ResolutionAgent** – Propose remediation steps.
4. **OpsLogAgent** – Persist results and decisions.

This spec defines functional behavior and tasks needed to implement the system.

---

# Functional Requirements

## Monitor Stage
- Parse log/metric input.
- Identify error-level patterns or anomalies.
- Output a list of `alert_events`.

## Triage Stage
- Accept `alert_events`.
- Determine:
  - severity level (Critical, High, Medium, Low)
  - category (Performance, Network, Storage, Application)
- Output: `incident_priority`, `category`.

## Resolution Stage
- Accept triage results.
- Use mapping rules or heuristics to suggest remediation steps.
- Output: `resolution_plan`.

## Logging Stage
- Accept resolution plan.
- Generate structured audit entry:
  - timestamp
  - stage outputs
  - agent execution order
  - summary of recommendations

---

# Data Flow
```
logs → MonitorAgent → alert_events
alert_events → TriageAgent → incident_priority, category
incident_priority + category → ResolutionAgent → resolution_plan
resolution_plan → OpsLogAgent → log_entry
```

---

# Tasks

## Agent Implementation Tasks
- [x] Implement **MonitorAgent.run()** to parse logs and detect anomalies.
- [x] Implement **TriageAgent.run()** for severity & category classification.
- [x] Implement **ResolutionAgent.run()** to propose remediation actions.
- [x] Implement **OpsLogAgent.run()** to generate audit log entry.

## Orchestrator Tasks
- [x] Ensure strict sequential data flow across agents.
- [x] Add top-level logging to show each stage execution.

## Hook Integration Tasks (Optional Enhancements)
- [ ] Integrate metrics parsing using `metrics_hook`.
- [ ] Integrate external alerting via `alert_api_hook`.
- [ ] Integrate incident ticketing through `jira_hook`.

## Testing & Execution Tasks
- [ ] Ensure entire pipeline executes using:
  ```
  python3 -m ui.console_client
  ```
- [ ] Add minimal sample logs in `data/sample_logs.txt`.

---

# Acceptance Criteria
- Pipeline runs end-to-end without error.
- Each agent logs its activity using `self.log()`.
- Orchestrator prints a final combined result.
- Audit log entry is well-structured and repeatable.
- Hooks can be plugged in without modifying agent internals.

---

# Notes for Kiro
- Follow steering rules defined in `.kiro/steering/`.
- Use incremental edits when adding or modifying code.
- Maintain absolute import paths.
