"""
Governance Page

Displays risk scoring, escalation decisions, and compliance analysis from pipeline executions.
Shows governance analysis results with collapsible details.
"""

import streamlit as st
import json
from pathlib import Path
from typing import Dict, List, Any


def get_output_log_path() -> Path:
    """
    Get the path to the output log file.
    
    Returns:
        Path: Path object pointing to data/output_log.json
    """
    project_root = Path(__file__).parent.parent.parent
    return project_root / "data" / "output_log.json"


def load_pipeline_history() -> List[Dict[str, Any]]:
    """
    Load pipeline execution history from output log.
    
    Returns:
        List[Dict]: List of pipeline execution records
    """
    log_path = get_output_log_path()
    
    if not log_path.exists():
        return []
    
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        st.error(f"Error loading pipeline history: {str(e)}")
        return []


def get_latest_governance_data(history: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Extract the most recent governance analysis from pipeline history.
    
    Note: Currently, governance analysis is not persisted to the output log by OpsLogAgent.
    This function will return empty governance data until the persistence layer is updated.
    
    Args:
        history: List of pipeline execution records
        
    Returns:
        Dict: Latest governance analysis data or empty dict
    """
    if not history:
        return {}
    
    # Get the most recent execution
    latest = history[-1]
    
    # Check if governance data exists in the record
    # (This will be empty until OpsLogAgent is updated to persist governance data)
    governance_analysis = latest.get('governance_analysis', {})
    audit_summary = latest.get('audit_summary', {})
    
    governance_data = {
        'execution_timestamp': latest.get('execution_timestamp', 'N/A'),
        'total_incidents': latest.get('total_incidents', 0),
        'governance_analysis': governance_analysis,
        'audit_summary': audit_summary
    }
    
    return governance_data


def get_risk_color(risk_level: str) -> str:
    """
    Get color code for risk level display.
    
    Args:
        risk_level: Risk level string (low, medium, high, critical)
        
    Returns:
        str: Color name for Streamlit styling
    """
    risk_level = risk_level.lower()
    if risk_level == 'critical':
        return 'red'
    elif risk_level == 'high':
        return 'orange'
    elif risk_level == 'medium':
        return 'yellow'
    else:
        return 'green'


def get_risk_emoji(risk_level: str) -> str:
    """
    Get emoji for risk level display.
    
    Args:
        risk_level: Risk level string (low, medium, high, critical)
        
    Returns:
        str: Emoji representing the risk level
    """
    risk_level = risk_level.lower()
    if risk_level == 'critical':
        return '🔴'
    elif risk_level == 'high':
        return '🟠'
    elif risk_level == 'medium':
        return '🟡'
    else:
        return '🟢'


# Page configuration
st.title("⚖️ Governance")
st.markdown("Risk scoring, escalation decisions, and compliance analysis from pipeline executions.")
st.markdown("---")

# Load pipeline history
history = load_pipeline_history()

# Handle empty history
if not history:
    st.warning("⚠️ No pipeline execution history found")
    st.info(f"Expected location: `{get_output_log_path()}`")
    st.markdown("""
    **To generate governance data:**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Return to this page to view governance analysis
    """)
    st.stop()

# Get latest governance data
governance_data = get_latest_governance_data(history)
governance_analysis = governance_data.get('governance_analysis', {})

# Check if governance analysis exists
if not governance_analysis:
    st.warning("⚠️ Governance data is not currently persisted to the output log")
    
    st.markdown("### Why is governance data not showing?")
    st.markdown("""
    The current pipeline architecture has the following flow:
    1. **MonitorAgent** → Detects incidents
    2. **TriageAgent** → Classifies incidents  
    3. **LLMResolutionAgent** → Generates resolution plans
    4. **OpsLogAgent** → Persists audit log (you are here)
    5. **LLMGovernanceAgent** → Analyzes risk and compliance
    6. **NotificationAgent** → Sends notifications
    
    Since OpsLogAgent runs **before** LLMGovernanceAgent, governance data is not included in the persisted output log.
    """)
    
    st.markdown("### How to view governance analysis")
    st.info("""
    **Option 1: View in Pipeline Runner (Real-time)**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Expand the "⚖️ Governance & Risk Analysis" section
    
    **Option 2: Future Enhancement**
    - Update the pipeline to persist governance data after it's generated
    - Modify OpsLogAgent to accept and persist governance output
    - This page will then display historical governance trends
    """)
    
    # Show what data IS available
    st.markdown("---")
    st.markdown("### Available Data")
    st.markdown(f"""
    The output log contains {len(history)} pipeline execution(s) with:
    - Incident counts and distributions
    - Resolution plans and priorities
    - Agent execution metadata
    
    But governance analysis (risk scores, escalation decisions, compliance issues) is not yet persisted.
    """)
    
    st.stop()

# Display execution metadata
st.subheader("📊 Latest Governance Analysis")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Execution Time", governance_data.get('execution_timestamp', 'N/A'))

with col2:
    st.metric("Total Incidents", governance_data.get('total_incidents', 0))

with col3:
    risk_level = governance_analysis.get('risk', 'unknown')
    risk_emoji = get_risk_emoji(risk_level)
    st.metric("Risk Level", f"{risk_emoji} {risk_level.capitalize()}")

st.markdown("---")

# Risk Score Section
st.subheader("🎯 Risk Assessment")

risk_level = governance_analysis.get('risk', 'unknown')
risk_emoji = get_risk_emoji(risk_level)

# Display risk level with appropriate styling
if risk_level.lower() == 'critical':
    st.error(f"{risk_emoji} **Risk Level: {risk_level.upper()}**")
    st.markdown("⚠️ **Immediate attention required**")
elif risk_level.lower() == 'high':
    st.warning(f"{risk_emoji} **Risk Level: {risk_level.upper()}**")
    st.markdown("⚠️ **Elevated risk - prompt action recommended**")
elif risk_level.lower() == 'medium':
    st.info(f"{risk_emoji} **Risk Level: {risk_level.capitalize()}**")
    st.markdown("ℹ️ **Moderate risk - monitor closely**")
else:
    st.success(f"{risk_emoji} **Risk Level: {risk_level.capitalize()}**")
    st.markdown("✅ **System operating within acceptable parameters**")

st.markdown("---")

# Escalation Decision Section
st.subheader("📢 Escalation Decision")

escalation = governance_analysis.get('escalation', 'N/A')
st.markdown(f"**Recommended Action:** {escalation}")

# Display escalation guidance based on risk level
if risk_level.lower() in ['critical', 'high']:
    st.warning("⚠️ Escalation recommended based on risk assessment")
else:
    st.info("ℹ️ No immediate escalation required")

st.markdown("---")

# Compliance Issues Section
st.subheader("📋 Compliance Analysis")

compliance_issues = governance_analysis.get('compliance_issues', [])

if compliance_issues:
    st.warning(f"⚠️ **{len(compliance_issues)} compliance issue(s) identified**")
    
    for idx, issue in enumerate(compliance_issues, 1):
        st.markdown(f"{idx}. {issue}")
else:
    st.success("✅ No compliance issues detected")

st.markdown("---")

# Commentary Section
st.subheader("💬 Governance Commentary")

commentary = governance_analysis.get('commentary', 'No commentary available')
st.markdown(commentary)

st.markdown("---")

# Collapsible Details Section
with st.expander("🔍 View Full Governance Data", expanded=False):
    st.json(governance_analysis)

# Audit Summary Section (if available)
audit_summary = governance_data.get('audit_summary', {})
if audit_summary:
    with st.expander("📝 View Audit Summary", expanded=False):
        st.json(audit_summary)

# Historical Governance Trends
st.markdown("---")
st.subheader("📈 Historical Governance Trends")

# Calculate historical statistics
risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
total_compliance_issues = 0

for record in history:
    # Check for governance_analysis directly in the record
    gov_analysis = record.get('governance_analysis', {})
    
    risk = gov_analysis.get('risk', 'unknown').lower()
    if risk in risk_counts:
        risk_counts[risk] += 1
    
    compliance = gov_analysis.get('compliance_issues', [])
    total_compliance_issues += len(compliance)

# Display historical metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", len(history))

with col2:
    critical_high_count = risk_counts['critical'] + risk_counts['high']
    st.metric("Critical/High Risk", critical_high_count)

with col3:
    st.metric("Total Compliance Issues", total_compliance_issues)

with col4:
    avg_compliance = total_compliance_issues / len(history) if history else 0
    st.metric("Avg Issues/Run", f"{avg_compliance:.1f}")

# Risk distribution chart
if any(risk_counts.values()):
    st.markdown("**Risk Level Distribution:**")
    
    # Create columns for risk distribution
    risk_cols = st.columns(4)
    
    for idx, (risk, count) in enumerate(risk_counts.items()):
        with risk_cols[idx]:
            emoji = get_risk_emoji(risk)
            st.metric(f"{emoji} {risk.capitalize()}", count)

# Footer
st.markdown("---")
st.caption("💡 Tip: Governance analysis is performed by the LLMGovernanceAgent after all other pipeline stages complete.")
