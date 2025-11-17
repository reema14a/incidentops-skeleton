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
- **Audit Logs** - View pipeline execution logs *(Coming Soon)*
- **Dashboards** - Visualize incident metrics and trends *(Coming Soon)*
- **Governance** - Review risk scores and compliance *(Coming Soon)*
- **Notifications** - Monitor notification channels and delivery status *(Coming Soon)*

### Getting Started

1. Use the sidebar to navigate to the **Pipeline Runner**
2. Enter log data or upload a log file
3. Click "Run Pipeline" to process incidents
4. View agent outputs and download results

### About the Pipeline

The system orchestrates intelligent agents in sequence:

1. **MonitorAgent** - Scans logs/metrics for anomalies
2. **TriageAgent** - Classifies incidents by severity and type
3. **LLM Alert Summary Agent** - Generates structured summaries
4. **LLM Resolution Agent** - Suggests remediation actions
5. **LLM Governance Agent** - Assesses risk and compliance
6. **NotificationAgent** - Delivers alerts via configured channels
7. **OpsLogAgent** - Records decisions for traceability

---

*IncidentOps Skeleton - AI-Powered Incident Management*
""")

# Footer
st.sidebar.markdown("---")
st.sidebar.info("IncidentOps v1.0")
