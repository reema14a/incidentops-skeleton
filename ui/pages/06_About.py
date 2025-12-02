"""
IncidentOps Streamlit UI - Home Page

This is the main entry point for the Streamlit multipage application.
Run with: streamlit run ui/Home.py
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="IncidentOps",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Main content
st.title("🚨 IncidentOps")
st.markdown("---")

st.markdown("""
## Welcome to IncidentOps

An AI-powered incident management framework that automates detection, triage, and resolution of system incidents.

### Available Features

Navigate using the sidebar to access:

- **Pipeline Runner** - Execute the incident management pipeline with log input
- **Audit Logs** - View pipeline execution logs
- **Dashboards** - Visualize incident metrics and trends
- **Governance** - Review risk scores and compliance
- **Notifications** - Configure channels and review delivery history

### 💡 Quick Start

1. Go to **Pipeline Runner**
2. Upload or paste logs
3. Run pipeline
4. View Governance, Audit, and Notifications for full system insights

### About the Pipeline

The system orchestrates intelligent agents in sequence:

1. **MonitorAgent** – Scans logs for anomalies  
2. **TriageAgent** – Classifies incidents by severity and category  
3. **AlertSummarizerAgent (LLM)** – Generates structured alert summaries  
4. **ResolutionAgent (LLM)** – Suggests remediation and resolution steps  
5. **GovernanceInsightsAgent (LLM)** – Identifies deeper risks and compliance signals  
6. **GovernanceAgent (LLM)** – Produces final risk score, escalation, and compliance assessment  
7. **NotificationAgent** – Sends alerts through configured notification channels


---

*IncidentOps Skeleton - AI-Powered Incident Management*
""")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("IncidentOps v1.0")
st.caption("IncidentOps v1.0 · Kiro Hackathon Edition")


st.caption("✨ Powered by Kiro — End-to-end AI-assisted Incident Intelligence and Governance.")
