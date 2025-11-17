---

# 🦴 IncidentOps Skeleton

### “Bringing Dead Systems Back to Life with AI-Powered Incident Management”

A spec-driven, multi-agent framework for automated **incident detection, triage, and resolution** — built entirely inside **Kiro IDE** using its **vibe coding, hooks, and MCP orchestration** features.

---

## 🚀 Overview

Modern DevOps teams drown in alerts and logs. IncidentOps Skeleton revives system observability by orchestrating a set of intelligent agents that detect, classify, and recommend fixes for incidents in real time.

Built for the **Kiroween Hackathon 👻** by leveraging **Kiro’s agentic IDE**, structured specs, and reproducible workflows.

---

## 🧩 Architecture

MonitorAgent  →  TriageAgent  →  ResolutionAgent  →  OpsLogAgent
(logs)            (severity)        (remediation)     (trace)

* **MonitorAgent** – Scans system logs or metrics for anomalies
* **TriageAgent** – Classifies incidents by severity & type
* **ResolutionAgent** – Suggests fixes or automation runbooks
* **OpsLogAgent** – Records every decision for traceability

Each agent is defined declaratively in `specs/agents.yaml` and orchestrated via Kiro hooks.

---

## ⚙️ Tech Stack

| Layer         | Tool              | Purpose                          |
| ------------- | ----------------- | -------------------------------- |
| Language      | Python 3.10+      | Agent logic                      |
| IDE           | **Kiro**          | Spec-driven, agentic development |
| Config        | YAML              | Agent + workflow definitions     |
| Integration   | MCP Hooks         | Log parsing, alert simulation    |
| UI            | Streamlit         | Optional web interface           |
| Governance    | JSON logs         | Traceability and explainability  |

---

## 🧠 Kiro Features Demonstrated

| Kiro Capability | How Used                                                       |
| --------------- | -------------------------------------------------------------- |
| **Vibe Coding** | Generated agent classes & workflow orchestration via Kiro chat |
| **Specs**       | `specs/agents.yaml` defines agent I/O and descriptions         |
| **MCP Hooks**   | Connected mock log parser (`metrics_hook.py`) and alert system |
| **Steering**    | Adjusted agent priorities dynamically during run               |
| **Governance**  | Every decision logged via OpsLogAgent for audit & replay       |

🎥 Demo Video: `demo/vibe-coding.mp4`
Shows Kiro chat-to-code flow: from YAML spec → generated agent → live execution.

---

## 🛡️ AI Governance Practices

IncidentOps Skeleton integrates lightweight governance principles:

* ✅ **Traceability:** Logs every decision with timestamp and agent name
* ✅ **Reproducibility:** All configs versioned in YAML specs
* ✅ **Auditability:** Generates `governance_summary.json` after each run
* ✅ **Explainability:** Each agent returns reasoning strings
* ✅ **Accountability:** Clear agent ownership for every action

---

## 📦 Setup

**Step 1:** Install dependencies
`pip install -r requirements.txt`

**Step 2:** Configure environment variables (optional)
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

**Step 3:** Run the pipeline

**Option A: CLI Mode**
```bash
python3 -m ui.console_client
```

**Option B: Streamlit UI**
```bash
streamlit run ui/Home.py
```

**Sample CLI output:**
[🦴 MonitorAgent] Detected 3 alerts.

[💀 TriageAgent] Severity: High | Category: Database

[⚡ ResolutionAgent] Suggested: Restart DB service

[🎃 OpsLogAgent] Incident logged successfully.

---

## ⚙️ Configuration

IncidentOps uses a centralized configuration system with priority-based resolution:

1. **Environment Variables** (highest priority) - Set in `.env` or system environment
2. **YAML Configuration** - Defined in `config/settings.yaml`
3. **Secure Defaults** (lowest priority) - Built-in fallback values

**Key Configuration Files:**
- `config/settings.yaml` - Runtime settings, paths, log levels
- `config/prompts.yaml` - LLM prompt templates
- `.env` - Secrets and environment-specific settings (not committed to git)

**Configuration Policy:**
All code must access configuration through `config.settings_loader`:

```python
from config.settings_loader import get_settings

settings = get_settings()
api_key = settings.get_openai_api_key()
```

Direct access to environment variables or YAML files is prohibited. See `docs/configuration_enforcement.md` for details.

**Validation:**
```bash
python3 scripts/validate_config_access.py
```

---

## 🔮 Future Enhancements

* Connect to real metrics (CloudWatch, Prometheus)
* Add LLM-based summarization of incidents
* Integrate with Jira / Slack via MCP hooks
* Extend to FIBO (visual incident storyboards)

---

## 🧙 Author

**Reema Raghava**

*AI + BI + Ops Systems Architect*

LinkedIn: https://www.linkedin.com/in/reema-raghava-28737a11/

GitHub: https://github.com/reema14a
---

