---
name: IncidentOps AIOps Pipeline
status: draft
description: Specification for the multi-agent IncidentOps system with AI-enhanced summarization, remediation, governance, logging, notifications, and Streamlit UI.
---

# Overview

IncidentOps is a sequential multi-agent AIOps pipeline. The system processes logs, detects anomalies, summarizes alerts, classifies severity, generates remediation guidance, maintains an audit log, performs governance checks, and sends notifications through an MCP-connected notification system.

Pipeline order:

1. MonitorAgent – Detect anomalies.
2. LLMAlertSummaryAgent – Produce human-friendly summaries.
3. TriageAgent – Assign severity/category deterministically.
4. LLMResolutionAgent – Generate AI-based remediation guidance.
5. OpsLogAgent – Produce factual audit logs with no interpretation.
6. LLMGovernanceAgent – Perform risk scoring, escalation, compliance.
7. GovernanceInsightsAgent(LLM) – Analyze historical DB trends and patterns.
8. NotificationAgent – Send alerts via MCP (email, push, etc.).


# Functional Requirements

## Monitoring
- Parse logs and extract anomalies.
- Output: `alert_events` list.

## Alert Summarization (AI)
- Summarize anomalies to natural language.
- Output: `summary_result` JSON.

## Triage
- Determine severity and category using deterministic logic.
- Output: `severity`, `category`.

## Remediation (AI)
- Produce remediation summaries with recommended actions.
- Output: `resolution_summary`, `top_actions`.

## Audit Logging
- Generate factual non-interpretive audit entries.
- Output: full structured audit record.

## Governance (AI)
- Score risk.
- Determine escalation needs.
- Add compliance and SLA implications.
- Output: `governance_result`.

## GovernanceInsightsAgent (AI, NEW)
- Analyzes historical governance data stored in the DB.
- Aggregation is performed by DB utility functions; the agent only interprets aggregated data.
- Inputs: get_risk_trend(), get_compliance_trend(), get_escalation_text_counts(), get_recent_runs(),get_category_distribution(), get_severity_distribution()
- Outputs JSON with: trend_summary, risk_trend, compliance_trend, recurring_issues, category_hotspots, recommendations, anomaly_detection.
- Runs after GovernanceAgent and before NotificationAgent.
- Persist GovernanceInsightsAgent output into insights_history ( ensure orchestrator writes insights_data + timestamp to DB)

## Notifications
- Use MCP tools to send notifications.
- Trigger only when escalation or governance criteria require it.
- NotificationAgent must support multiple notification channels defined in settings:
`settings.notification.channels` → list of channels such as ["gmail", "pushover"]

- Each channel maps to an MCP tool:

  - gmail  →  gmail.send
  - pushover → pushover.send
  <!-- - slack (optional future) → slack.send -->

- NotificationAgent must:
  - Loop through enabled channels
  - Call MCPClient.call_tool(tool_name, params)
  - Build params from the pipeline summary, severity, and governance outputs
  - Use dependency injection so tests can provide a mocked MCPClient.


# Data Flow

`logs → MonitorAgent → LLMAlertSummaryAgent → TriageAgent → LLMResolutionAgent
→ OpsLogAgent → LLMGovernanceAgent → GovernanceInsightsAgent → NotificationAgent`

# Tasks

## Agent Implementation
- [x] MonitorAgent
- [x] LLMAlertSummaryAgent
- [x] TriageAgent
- [x] LLMResolutionAgent
- [x] OpsLogAgent
- [x] LLMGovernanceAgent

---

## Refactor Tasks
- [x] Remove legacy rule-based ResolutionAgent.
- [x] Validate separation between OpsLogAgent and GovernanceAgent.
- [x] Move openai_client.py into `llm/` and update imports.

---

## Logging Tasks
- [x] Update BaseAgent.log() to log to console + `logs/pipeline.log`.
- [x] Create logs/ directory.
- [x] Add rotating file handler (5MB, keep 3 backups).

---

## LLM Logging Tasks
- [x] Add structured logging to llm/openai_client.py (metadata, parsing, errors).
- [x] Ensure failures propagate to pipeline.log.

---

## Settings Loader Tasks
- [x] Create `config/settings_loader.py`.
- [x] Load configuration in priority:
      1. Environment variables (e.g., MCP_ENDPOINT)
      2. settings.yaml
      3. Secure defaults
- [x] Expose typed accessors, including:
      - `get_mcp_endpoint()`
      - `get_mcp_timeout()`
      - `get_notification_channels()`
- [x] Enforce rule: secrets must come only from environment variables.
- [x] Validate required settings and raise structured errors.
- [x] Disallow direct env/yaml reading inside agents.
- [x] Support viaSocket MCP by accepting HTTP/S endpoints:
      - If endpoint contains `.viasocket.com`, treat HTTP/S as valid.
      - Do not enforce or convert WebSocket protocol.
      - Pass endpoint to MCPClient unchanged.

---

## Notification Tasks
- [x] Implement NotificationAgent using MCPClient.
- [x] Insert into pipeline after GovernanceAgent. NotificationAgent must gracefully handle tool failures via MCPToolError and log them without stopping the pipeline.
- [x] Add end-to-end test for notification delivery.

---

## GovernanceInsightsAgent Tasks (Phase 2)
- [x] Implement GovernanceInsightsAgent (LLM-based historical analysis)
- [x] Add orchestrator step after LLMGovernanceAgent
- [x] Orchestrator must call new DB aggregation APIs and pass results to the agent

---

## AI Framework Tasks (Optional)
- [ ] Lightweight LangGraph state modeling inside GovernanceAgent.
- [ ] Export flow visualization (JSON or DOT).
- [ ] Optional minimal LangGraph version of pipeline.
- [ ] Implement hooks for guardrails.

---

## Other Improvements
- [ ] Add caching (@st.cache_data) for heavy DB reads to improve UI responsiveness.

## Testing Tasks
- [ ] Update tests for all LLM agents (mocking OpenAIClient).
- [ ] Full pipeline integration tests.
- [ ] Tests ensuring OpsLogAgent has zero governance logic.

# Acceptance Criteria

- Full pipeline runs with `python3 -m ui.console_client`.
- OpsLogAgent produces factual-only logs.
- All LLM agents use JSON parser utilities.
- Rotating logs saved to logs/pipeline.log.
- GovernanceAgent outputs include risk, escalation, compliance.
- GovernanceInsightsAgent produces historical insights using DB aggregation APIs.
- NotificationAgent fires when escalation is required.
- Streamlit UI fully operational.

# Notes for Kiro

- Maintain absolute imports.
- Follow `.kiro/steering/standards.md` & `.kiro/steering/structure.md`.
- Use incremental steps for refactors or UI code.
- MCP endpoint handling must support viaSocket HTTP/S endpoints exactly as provided.

