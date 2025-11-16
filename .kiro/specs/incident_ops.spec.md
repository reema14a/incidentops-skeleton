---
name: "IncidentOps AIOps Pipeline"
status: "draft"
description: "Specification for the multi-agent IncidentOps system with AI-enhanced summarization, remediation, governance, logging, MCP notifications, Streamlit UI, and optional LangGraph integration."
---

# Overview
IncidentOps is a sequential multi-agent AIOps pipeline. The system processes logs, detects anomalies, summarizes alerts, classifies severity, generates AI-based remediation guidance, writes audit logs, performs AI governance analysis, and later sends notifications using MCP. The updated pipeline stages are:

1. MonitorAgent – Detect raw anomalies in log or metric data.
2. LLMAlertSummaryAgent – Generate human-friendly summaries of alerts.
3. TriageAgent – Classify severity and category using deterministic logic.
4. LLMResolutionAgent – Generate AI-driven remediation summaries and recommended actions.
5. OpsLogAgent – Produce a factual, deterministic audit log without interpretation.
6. LLMGovernanceAgent – Perform risk scoring, escalation decisions, and compliance analysis.
7. NotificationAgent (Upcoming) – Send alerts via email or other MCP-based channels.

# Functional Requirements

## Monitoring
- Parse logs and extract anomalies.
- Output: alert_events list.

## Alert Summarization (AI)
- Summarize alerts in natural language.
- Output: summary_result JSON.

## Triage
- Assign severity and category deterministically.
- Output: severity, category.

## Remediation (AI)
- Produce human-friendly remediation summaries.
- Output: resolution_summary, top_actions.

## Audit Logging
- Write a complete factual audit record.
- No interpretation, no governance logic.

## Governance (AI)
- Perform risk scoring.
- Determine escalation requirements.
- Add compliance and SLA notes.
- Output: governance_result.

## Notifications (Future)
- Use MCP tools to send notifications (email, Slack, etc.) based on governance results.

# Data Flow

logs → MonitorAgent → LLMAlertSummaryAgent → TriageAgent → LLMResolutionAgent → OpsLogAgent → LLMGovernanceAgent → NotificationAgent (optional)

# Tasks

## Agent Implementation Tasks (Completed or Ongoing)
- [x] Implement MonitorAgent
- [x] Implement LLMAlertSummaryAgent
- [x] Implement TriageAgent
- [x] Implement LLMResolutionAgent
- [x] Implement OpsLogAgent with factual-only behavior
- [x] Implement LLMGovernanceAgent

## Refactor Tasks
- [x] Remove rule-based ResolutionAgent and update pipeline.
- [x] Ensure OpsLogAgent and LLMGovernanceAgent have non-overlapping responsibilities.
- [x] Move openai_client.py from agents/ into a new llm/ directory and update all imports.

## Logging Tasks
- [x] Modify BaseAgent.log() to write to both console and logs/pipeline.log.
- [x] Create a logs/ directory at project root for runtime log storage.
- [x] Use a rotating file handler (max 5 MB per file, retain 3 backups).

## LLM Service Logging Tasks
- [x] Add structured logging to llm/openai_client.py, including request metadata, response metadata, JSON parsing status, and fallback/error reporting.
- [x] Ensure all LLM-related failures are written to logs/pipeline.log using the shared logging configuration.

## Notification Tasks (Upcoming)
- [ ] Implement NotificationAgent using MCP (email or Slack).
- [ ] Insert NotificationAgent after LLMGovernanceAgent in the pipeline.
- [ ] Provide an end-to-end test validating notification delivery.

## UI Tasks (Streamlit Frontend)
- [ ] Create a Streamlit UI (ui/app.py) with:
      - Log input textbox
      - File upload option
      - Button to run the pipeline
      - Collapsible display of each agent's output
      - Final governance decision (risk, escalation, compliance)
      - Audit log viewer
      - Download button for pipeline output JSON
- [ ] Add a real-time log viewer reading from logs/pipeline.log.
- [ ] Add dashboard visualizations (severity breakdown, categories, timeline).
- [ ] Add a Governance tab with detailed scoring, SLA notes, and escalation guidance.
- [ ] Add a Notification tab to show delivery status and message previews.
- [ ] Ensure the UI does not break CLI execution via python3 -m ui.console_client.
- [ ] Add UI-specific test coverage (mock pipeline execution).

## AI Framework Tasks (Optional Enhancements)
- [ ] Add a lightweight LangGraph node inside LLMGovernanceAgent to simulate state transitions.
- [ ] Produce a state visualization (JSON or DOT) showing pipeline flow.
- [ ] (Optional) Implement a minimal LangGraph version of the pipeline to demonstrate compatibility.

## Testing Tasks
- [ ] Update unit tests for all LLM agents to use mock OpenAIClient.
- [ ] Update integration tests for the full AI pipeline.
- [ ] Add tests ensuring that OpsLogAgent does not perform any governance logic.

# Acceptance Criteria
- Pipeline executes end-to-end using python3 -m ui.console_client.
- No interpretive logic exists in OpsLogAgent.
- All LLM agents use utils/json_parser.py for structured parsing.
- Logs are written to logs/pipeline.log via rotating handler.
- Governance output includes risk scoring, escalation logic, and compliance notes.
- NotificationAgent sends messages when escalation_required is true.
- Streamlit UI provides a full interactive experience around the pipeline.

# Notes for Kiro
- Maintain absolute import paths.
- Follow steering rules in .kiro/steering/standards.md and .kiro/steering/structure.md.
- Use incremental targeted edits when refactoring, moving files, or generating UI.
