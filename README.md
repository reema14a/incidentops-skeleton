# 🦴 **IncidentOps**

### **AI-Assisted Incident Detection, Triage & Governance — Built with Kiro’s Spec-Driven Workflow**

IncidentOps is a fully functional, multi-agent incident pipeline built for the **Kiro Hackathon**, designed to make recurring issues easier to see in noisy production environments. It uses **Kiro’s spec-driven development**, multi-agent orchestration, and clean iterative workflows to build a complete incident-management system in a fraction of the usual time.

---

## 🚀 **Overview**

In real operations, major incidents rarely begin with dramatic failures — they start as *small recurring signals* buried inside logs.
IncidentOps surfaces these patterns using a sequence of cooperating agents:

1. **MonitorAgent** – Detects anomalies in raw log entries
2. **LLMAlertSummaryAgent** – Produces human-friendly summaries
3. **TriageAgent** – Assigns deterministic severity + category
4. **LLMResolutionAgent** – Suggests AI-based remediation steps
5. **OpsLogAgent** – Writes factual audit logs (no interpretation)
6. **LLMGovernanceAgent** – Performs risk scoring, escalation, compliance
7. **LLMGovernanceInsightsAgent** – Analyzes recurring historical patterns
8. **NotificationAgent** – Sends alerts externally (email, push), if enabled

All runs are stored in a persistent **SQLite database**, and the system includes a multi-page **Streamlit UI** for interacting with pipeline results.

---

## 🧩 **Architecture Diagram**

> *Note: Render free-tier services may take 20–40 seconds to cold-start.*

![Architecture](docs/architecture.png)

---

## 🖥️ **How to Use the App**

1. **Open the deployed Streamlit app**
   *(Cold start may take 30–60 seconds)*
2. Go to **Home** to run a complete pipeline using sample logs
3. Navigate through sidebar pages:

   * **Pipeline Runner** → see each agent’s output
   * **Governance Insights** → view recurring patterns across runs
   * **Database View** → inspect persisted historical incidents
4. Run the pipeline multiple times — results persist in SQLite
5. Optionally test NotificationAgent if environment variables are set

---

## ⚙️ **Tech Stack**

| Layer         | Tool          | Purpose                                 |
| ------------- | ------------- | --------------------------------------- |
| Orchestration | Python        | Agent logic + pipeline execution        |
| UI            | Streamlit     | Multi-page frontend                     |
| Storage       | SQLite        | Fully persistent runs + analytics       |
| AI Reasoning  | LLMs (OpenAI) | Summaries, remediation, insights        |
| Development   | **Kiro IDE**  | Spec-driven, task-driven build workflow |

---

## 🧠 **Kiro Capabilities Used**

* **Spec-Driven Development**
  Wrote structured specs → Kiro generated modular agents & flows.

* **Start Task Workflow**
  Allowed clean, deterministic execution of each specification.

* **Vibe Coding**
  Used conversational refinement to evolve components iteratively.

* **Hooks & Triggers**
  Connected governance scoring + insights generation.

* **Steering Documents**
  Ensured reproducible generation across UI, DB, pipeline, and agents.

---

## 📦 **Local Setup**

### 1. Install dependencies

```
pip install -r requirements.txt
```

### 2. Set environment variables (optional but recommended)

```
OPENAI_API_KEY=your_key
EMAIL_USER=...
EMAIL_PASSWORD=...
```

### 3. Run Streamlit UI

```
streamlit run ui/Home.py
```

### 4. Directory Structure

Created automatically on first run:

```
data/db/              # SQLite persistence
data/sample_logs/     # Input samples
logs/                 # Agent + pipeline logs
```

---

## 🔮 **Future Enhancements**

* Plug into real observability sources (CloudWatch, Prometheus)
* Add AI-based correlation between incidents
* Extend governance scoring with risk thresholds
* Integrate outgoing notifications (Slack, PagerDuty, Jira)

---

## 👤 **Author**

**Reema Raghava**
AI + BI + Ops Systems Architect

🔗 LinkedIn: [https://www.linkedin.com/in/reema-raghava-28737a11/](https://www.linkedin.com/in/reema-raghava-28737a11/)
🔗 GitHub: [https://github.com/reema14a](https://github.com/reema14a)

---
