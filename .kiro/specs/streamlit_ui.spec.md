---

name: Streamlit UI for IncidentOps
status: draft
description: Specification for a multi-page Streamlit UI built in strict phases.
---

# 🔒 **Important Kiro Instruction (Read First)**

> **Kiro must only create files when the corresponding task with `- [ ]` is executed.**
>
> **Do NOT create pages, components, or additional files based on examples in this spec.**
>
> **In Phase 1, Kiro must create ONLY:**
>
> * `ui/Home.py`
> * The empty folders:
>
>   * `ui/pages/`
>   * `ui/components/`
>
> **All other files must be created later ONLY when their specific tasks are executed.**

---

# **Overview**

This spec defines the phased development of a Streamlit UI for IncidentOps.
The UI must provide:

* A pipeline runner
* Logs viewer
* Dashboards
* Governance & notification visibility

UI must remain optional and must not interfere with CLI execution.

---

# **UI Architecture**

### **Framework**

* Streamlit multipage app (run via `streamlit run ui/Home.py`)

### **Folder Structure (initial minimal structure only)**

```
ui/
  Home.py               # Created in Phase 1
  pages/                # EMPTY — pages created in later phases only
  components/           # EMPTY — components created later
```

**Kiro Reminder:**

> Do NOT create any files inside `pages/` or `components/` during Phase 1.

### **Backend Integration**

* UI will call `run_pipeline(log_text, file_input=None)`
* Never call agents directly
* UI is a thin interface; pipeline remains in backend

---

# **Planned Pages (for reference only)**

> **These pages must NOT be created until their tasks are reached.**

* Pipeline Runner
* Audit Logs
* Dashboards
* Governance
* Notifications

---

# **UI Phases**

### **Phase 1 — MVP (Pipeline Runner Only)**

* Build minimal structure + Pipeline Runner UI
* Enable pipeline execution + agent output viewer

### **Phase 2 — Logs & Observability**

* Create Audit Logs page & real-time log viewer

### **Phase 3 — Dashboards**

* Severity, category, and timeline charts

### **Phase 4 — Governance**

* Governance summary + compliance
* Governance Page Architecture
```
Governance Page
 ├── Overview Tab  
 │     - Summary card (risk, escalation, compliance count)
 │     - Timestamp, run ID
 │     - Compact JSON expander
 │
 ├── Historical Tab  (DB analytics)
 │     - Governance history table
 │     - Risk trend charts
 │     - Escalation frequency charts
 │     - Compliance trend charts
 │     - Category distribution charts
 │     - Severity distribution charts
 │     - Per-run JSON expanders
 │
 └── AI Insights Tab (LLM)
       - trend_summary
       - recurring issues
       - category hotspots
       -  compliance_trend
       - risk_trend
       - recommendations
       - anomaly_detection
       - raw JSON
```

### **Phase 5 - Governance Page – AI Insights Tab (NEW)**

* Displays results from GovernanceInsightsAgent as mentioned in above architecture 
  * Trend Summary
  * Recurring Issues
  * Category Hotspots
  * Compliance Trend
  * Risk Trend
  * Recommendations
  * Anomaly Detection
  * Raw JSON
  
### **Phase 6 — Notifications**

* Notification channel/status viewer
* Support configuration of multiple Gmail recipients.
* Show recent notification events.
* Provide "Send Test Notification".

### **Phase 7 — Navigation Improvements**
- Dashboards set as default landing page.
- Home functions as Navigation Hub.
- Pipeline Runner displays links to Governance, Audit Logs, Notifications after execution.

### **Phase 8 — UI Tests**

* Page rendering tests
* Mock pipeline tests
* Dashboard tests

---

# **Tasks (Kiro Executable Tasks)**

## **Phase 1 — Pipeline Runner MVP**

### Folder & entrypoint

* [x] Create minimal Streamlit multipage structure under `ui/`:

  * `ui/Home.py`
  * empty folder `ui/pages/`
  * empty folder `ui/components/`
* [x] Implement `Home.py` with introduction + navigation

### Pipeline Runner Page

> Note: This page must be created under `ui/pages/` **ONLY when this block is executed**.

* [x] Create `ui/pages/Pipeline_Runner.py`
* [x] Add log input field
* [x] Add file upload field
* [x] Add “Run Pipeline” button
* [x] Add collapsible sections for each agent output
* [x] Add JSON output download
* [x] Integrate backend `run_pipeline()`
* [x] Ensure UI does not break CLI pipeline execution

---

## **Phase 2 — Logs & Observability**

> Create these only when this phase starts.

* [x] Create `ui/pages/Audit_Logs.py`
* [x] Implement viewer for `logs/pipeline.log`
* [x] Add real-time log streaming (polling)
* [x] Add log formatting + truncation
* [x] Handle missing or empty log file gracefully
* [x] Add link after View Logs  section to go back to Top (since View Log section could be long)

---

## **Phase 3 — Dashboards**

> Components must be created ONLY when this phase is active.

* [x] Create `ui/pages/Dashboards.py`
* [x] Generate severity breakdown chart
* [x] Generate category distribution chart
* [x] Generate timeline chart (if timestamps exist)
- [x] Refactor Dashboards page to use reusable chart components from ui/components/charts.py
- [x] Add tabular options at top of page after summary for each chart isntead of scrolling through the page
- [x] Make Insights as the first default tab. 
- [x] Add "Refresh" button to right side of the page after section name
- [x] Add optional auto-refresh interval selector
- [ ] Add a timeline filter to the Dashboard page:
      - Implement a date range selector (start_date, end_date)
      - Filter DB-backed dashboard metrics using the selected range
      - Refresh the severity, category, and timeline charts based on filtered results
      - Support “All Time” view
      - Gracefully handle when no runs fall within the selected range

---

## **Phase 4 — Governance**

* [x] Create `ui/pages/Governance.py`
* [x] Display risk level
* [x] Display escalation decision
* [x] Fix Governance page to use values from governance_data JSON:
      - Parse governance_data JSON for risk, escalation, commentary, compliance_issues, risk_score, extra_metadata, and additional_context
      - Display Pipeline Run ID in the main metadata row
      - Do not rely on legacy columns (risk, escalation, commentary)
* [ ] Enhance Governance analytics UI:
      - Add governance history table
      - Add risk/escalation/compliance trend charts
      - Add severity & category distribution charts
      - Add Key Observations summary
      - Add per-run JSON expanders
* [ ] Redesign Governance layout (Summary Card, Overview tab, Historical tab, collapsible history)

---
## **Phase 5 — Governance Insights**
- [ ] Add AI Insights tab to Governance page with three sections:
      - Summary Insights (trend_summary)
      - Patterns (recurring_issues, hotspots)
      - Recommendations + anomalies
- [ ] Display output of GovernanceInsightsAgent
- [ ] Add JSON expander for insights output
- [ ] Add DB-backed trend charts (risk, compliance, escalation)


## **Phase 6 — Notifications**

* [ ] Create `ui/pages/Notifications.py`
* [ ] Show enabled channels from settings
* [ ] Show last notification results
* [ ] Show success/error messages
- [ ] Implement Notifications page
- [ ] Add field for configuring multiple Gmail recipient emails
- [ ] Display list of recent notification events from DB
- [ ] Add "Send Test Notification" action

---

## **Phase 7 — Navigation Improvements**

- [ ] Set Dashboards as default landing page instead of Home
- [ ] Convert Home page into Navigation Hub
- [ ] Add navigation buttons from Pipeline Runner to Governance, Audit Logs, and Notifications

---

## **Phase 8 — UI Tests**

* [ ] Add UI tests for Pipeline Runner
* [ ] Add UI tests for Audit Logs
* [ ] Add UI tests for Dashboards
* [ ] Add UI tests for Governance
* [ ] Add UI tests for Notifications
* [ ] Add mock pipeline fixture for testing
* [ ] Ensure UI tests run independently (no real LLM calls)

---

# **Acceptance Criteria**

* Streamlit UI runs via `streamlit run ui/Home.py`
* Only Phase 1 files exist during Phase 1
* No future pages/components created early
* Pipeline runs correctly from UI
* Real-time logs work
* Dashboards render cleanly
* Governance & notification pages functional
* Create UI validation tests under tests/ui
* No need to delete UI validation tests
* No secrets exposed

---
