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

### **Phase 4 — Governance & Notifications**

* Governance summary + compliance
* Notification channel/status viewer

### **Phase 5 — UI Tests**

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

* [ ] Create `ui/pages/3_Dashboards.py`
* [ ] Create `ui/components/charts.py`
* [ ] Generate severity breakdown chart
* [ ] Generate category distribution chart
* [ ] Generate timeline chart (if timestamps exist)

---

## **Phase 4 — Governance**

* [ ] Create `ui/pages/4_Governance.py`
* [ ] Display risk score
* [ ] Display escalation decision
* [ ] Display compliance issues
* [ ] Add collapsible governance details

---

## **Phase 5 — Notifications**

* [ ] Create `ui/pages/5_Notifications.py`
* [ ] Show enabled channels from settings
* [ ] Show last notification results
* [ ] Show success/error messages

---

## **Phase 6 — UI Tests**

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
* UI tests pass
* No secrets exposed

---
