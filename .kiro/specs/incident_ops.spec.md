---
name: IncidentOps System
status: draft
description: Multi-agent AIOps pipeline for monitoring, triage, resolution, and governance
---

# Requirements

## Overview
This project implements an AI-assisted AIOps workflow using multiple Python agents orchestrated sequentially:
Monitor → Triage → Resolution → OpsLog

The system reads logs, classifies incidents, generates resolution plans, and maintains audit logs.

## Components

### Agents
| Agent | Purpose |
|-------|---------|
| MonitorAgent | Scans logs/metrics and outputs alert events |
| TriageAgent | Classifies alerts by severity and category |
| ResolutionAgent | Generates remediation recommendations |
| OpsLogAgent | Logs final output, governance tracking |

# Design

## Architecture
- Python-based agent modules in `/agents/`
- Orchestrator pipeline in `/orchestrator/`
- Optional hooks in `/hooks/`
- Configuration-driven via `/config/`
- UI entry point via `ui/console_client.py`

# Implementation

## Tasks
- [x] Implement MonitorAgent (Python)
- [x] Implement TriageAgent
- [ ] Implement ResolutionAgent
- [ ] Implement OpsLogAgent
- [ ] Build orchestrator pipeline
- [ ] Add audit logging
- [ ] Integrate hooks
- [ ] Add Gradio UI
