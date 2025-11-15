---
inclusion: always
---

# Product Overview

IncidentOps Skeleton is an AI-powered incident management framework that automates detection, triage, and resolution of system incidents.

## Core Purpose

Orchestrate intelligent agents to process system logs and metrics, classify incidents by severity, recommend remediation actions, and maintain audit trails for governance.

## Agent Pipeline

The system follows a sequential multi-agent workflow:

1. **MonitorAgent** - Scans logs/metrics for anomalies
2. **TriageAgent** - Classifies incidents by severity and type
3. **ResolutionAgent** - Suggests fixes or automation runbooks
4. **OpsLogAgent** - Records decisions for traceability

## Key Principles

- **Traceability**: Every decision logged with timestamp and agent name
- **Reproducibility**: All configurations versioned in YAML
- **Explainability**: Agents return reasoning strings for their actions
- **Accountability**: Clear agent ownership for every action
