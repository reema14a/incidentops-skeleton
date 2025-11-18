"""
Governance Page

Displays risk scoring, escalation decisions, and compliance analysis from pipeline executions.
Shows governance analysis results with collapsible details.
"""

import streamlit as st
import sys
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import database utilities
from db import db_util


def get_latest_governance_data() -> Dict[str, Any]:
    """
    Extract the most recent governance analysis from the database.
    
    Returns:
        Dict: Latest governance analysis data or empty dict
    """
    # Get the most recent governance analysis from the database
    governance_history = db_util.get_governance_history(limit=1)
    
    if not governance_history:
        return {}
    
    latest = governance_history[0]
    
    # Get the associated pipeline run details
    pipeline_runs = db_util.get_pipeline_runs(limit=1)
    
    if not pipeline_runs:
        return {}
    
    latest_run = pipeline_runs[0]
    
    # Parse governance_data JSON if available
    governance_analysis = {}
    if latest.get('governance_data'):
        try:
            governance_analysis = json.loads(latest['governance_data'])
        except json.JSONDecodeError:
            # Fallback to legacy columns if JSON parsing fails
            governance_analysis = {
                'risk': latest.get('risk', 'unknown'),
                'escalation': latest.get('escalation', 'N/A'),
                'commentary': latest.get('commentary', 'No commentary available'),
                'compliance_issues': []
            }
    else:
        # Fallback to legacy columns if governance_data is not available
        governance_analysis = {
            'risk': latest.get('risk', 'unknown'),
            'escalation': latest.get('escalation', 'N/A'),
            'commentary': latest.get('commentary', 'No commentary available'),
            'compliance_issues': []
        }
    
    governance_data = {
        'execution_timestamp': latest.get('timestamp', 'N/A'),
        'total_incidents': latest_run.get('alerts_count', 0),
        'governance_analysis': governance_analysis,
        'run_id': latest.get('run_id')
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

def format_timestamp(ts: str) -> str:
    if not ts or ts == "N/A":
        return "N/A"
    try:
        # Remove trailing Z if exists
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        return dt.strftime("%Y-%b-%d, %H:%M")
        # return dt.strftime("%d %b %Y, %I:%M %p")
    except:
        return ts  # fallback

def short_escalation(text: str) -> str:
    if not text: 
        return "N/A"
    words = text.strip().split()
    return " ".join(words[:2])

# Page configuration
st.title("⚖️ Governance")
st.markdown("Risk scoring, escalation decisions, and compliance analysis from pipeline executions.")
st.markdown("---")

# Get latest governance data from database
governance_data = get_latest_governance_data()

# Handle empty history
if not governance_data:
    st.warning("⚠️ No governance analysis found in database")
    st.markdown("""
    **To generate governance data:**
    1. Navigate to the **Pipeline Runner** page
    2. Run the pipeline with log input
    3. Return to this page to view governance analysis
    """)
    st.stop()

governance_analysis = governance_data.get('governance_analysis', {})

# Validate governance analysis data
if not governance_analysis or not governance_analysis.get('risk'):
    st.warning("⚠️ Governance analysis data is incomplete")
    st.info("The governance analysis may not have been fully generated during the pipeline run.")
    st.stop()

# Display execution metadata
st.subheader("📊 Latest Governance Analysis")

risk_level = governance_analysis.get('risk', 'unknown')
risk_emoji = get_risk_emoji(risk_level)


with st.expander(" Summary", expanded=True):
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Pipeline Run ID", f"#{governance_data.get('run_id', 'N/A')}")

    with col2:
        formatted_ts = format_timestamp(governance_data.get('execution_timestamp', 'N/A'))
        st.metric("Execution Time", formatted_ts)

    with col3:
        st.metric("Total Incidents", governance_data.get('total_incidents', 0))

    st.markdown("---")

    # ---- SECOND ROW ----
    compliance_issues = governance_analysis.get("compliance_issues", [])
    compliance_count = len(compliance_issues)

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric("Risk Level", f"{get_risk_emoji(risk_level)} {risk_level.capitalize()}")

    with col5:
        st.metric("Compliance Issues", compliance_count)

    with col6:
        escalation = short_escalation(governance_analysis.get("escalation"))
        st.metric("Escalation", escalation)

st.markdown("---")

# Risk Score Section
st.subheader("🎯 Risk Assessment")

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

# Get compliance issues from governance_data JSON first
compliance_issues_records = governance_analysis.get('compliance_issues', [])

# If not in JSON, fall back to database query
if not compliance_issues_records:
    run_id = governance_data.get('run_id')
    if run_id:
        # Query compliance issues for this specific run
        try:
            with db_util.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT issue
                    FROM compliance_issues
                    WHERE run_id = ?
                    ORDER BY id ASC
                """, (run_id,))
                rows = cursor.fetchall()
                compliance_issues_records = [row['issue'] for row in rows]
        except Exception as e:
            st.error(f"Error loading compliance issues: {str(e)}")

if compliance_issues_records:
    st.warning(f"⚠️ **{len(compliance_issues_records)} compliance issue(s) identified**")
    
    for idx, issue in enumerate(compliance_issues_records, 1):
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
    # Display the full governance_data JSON
    st.json(governance_analysis)
    
    # Display additional fields if they exist
    if governance_analysis.get('risk_score'):
        st.markdown("---")
        st.markdown(f"**Risk Score:** {governance_analysis.get('risk_score')}")
    
    if governance_analysis.get('extra_metadata'):
        st.markdown("---")
        st.markdown("**Extra Metadata:**")
        st.json(governance_analysis.get('extra_metadata'))
    
    if governance_analysis.get('additional_context'):
        st.markdown("---")
        st.markdown("**Additional Context:**")
        st.markdown(governance_analysis.get('additional_context'))

# Audit Summary Section (if available)
run_id = governance_data.get('run_id')
if run_id:
    with st.expander("📝 View Audit Summary", expanded=False):
        try:
            with db_util.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, count, timestamp, audit_data
                    FROM audit_summary
                    WHERE run_id = ?
                """, (run_id,))
                row = cursor.fetchone()
                
                if row:
                    audit_data = {
                        'status': row['status'],
                        'count': row['count'],
                        'timestamp': row['timestamp']
                    }
                    
                    # Include full JSON data if available
                    if row['audit_data']:
                        try:
                            audit_json = json.loads(row['audit_data'])
                            audit_data['full_audit'] = audit_json
                        except json.JSONDecodeError:
                            pass
                    
                    st.json(audit_data)
                else:
                    st.info("No audit summary available")
        except Exception as e:
            st.error(f"Error loading audit summary: {str(e)}")

# Historical Governance Trends
st.markdown("---")
st.subheader("📈 Historical Governance Trends")

# Get all governance history from database
all_governance = db_util.get_governance_history()
all_pipeline_runs = db_util.get_pipeline_runs()

# Calculate historical statistics
risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0, 'unknown': 0}

for record in all_governance:
    risk = record.get('risk', 'unknown')
    if risk:
        risk = risk.lower()
        if risk in risk_counts:
            risk_counts[risk] += 1
        else:
            risk_counts['unknown'] += 1

# Get compliance statistics from database
compliance_stats = db_util.get_compliance_stats()
total_compliance_issues = compliance_stats.get('total_issues', 0)

# Display historical metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", len(all_pipeline_runs))

with col2:
    critical_high_count = risk_counts['critical'] + risk_counts['high']
    st.metric("Critical/High Risk", critical_high_count)

with col3:
    st.metric("Total Compliance Issues", total_compliance_issues)

with col4:
    avg_compliance = compliance_stats.get('avg_issues_per_run', 0.0)
    st.metric("Avg Issues/Run", f"{avg_compliance:.1f}")

# Risk distribution chart
if any(risk_counts.values()):
    st.markdown("**Risk Level Distribution:**")
    
    # Create columns for risk distribution (exclude 'unknown' if it's 0)
    risk_levels = ['low', 'medium', 'high', 'critical']
    risk_cols = st.columns(4)
    
    for idx, risk in enumerate(risk_levels):
        count = risk_counts.get(risk, 0)
        with risk_cols[idx]:
            emoji = get_risk_emoji(risk)
            st.metric(f"{emoji} {risk.capitalize()}", count)

# Historical Governance Records
st.markdown("---")
st.subheader("📜 Historical Governance Records")

if all_governance:
    st.markdown(f"Showing {len(all_governance)} governance analysis record(s)")
    
    # Display governance records in a table-like format
    for idx, record in enumerate(all_governance):
        # Parse governance_data JSON for this record
        raw_json = record.get("governance_data", "") or ""
        clean_json = raw_json.strip().replace("\n", " ").replace("\r", " ")

        try:
            record_governance_analysis = json.loads(clean_json)
        except Exception:
            record_governance_analysis = {}


        risk_level = record_governance_analysis.get('risk', 'unknown')
        
        with st.expander(
            f"Run #{record.get('run_id')} - {record.get('timestamp', 'N/A')} - "
            f"{get_risk_emoji(risk_level)} {risk_level.capitalize()}",
            expanded=(idx == 0)  # Expand the first (most recent) record by default
        ):
            # Display normalized governance fields (JSON only)
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Risk Level:**")
                st.markdown(f"{get_risk_emoji(risk_level)} {risk_level.capitalize()}")

                st.markdown("**Escalation:**")
                st.write(record_governance_analysis.get("escalation", "N/A"))

            with col2:
                st.markdown("**Execution Time:**")
                st.write(record.get("timestamp", "N/A"))

                st.markdown("**Run ID:**")
                st.write(f"#{record.get('run_id')}")
            
            # Display commentary
            st.markdown("**Commentary:**")
            commentary = record_governance_analysis.get('commentary', 'No commentary available')
            st.markdown(commentary)
            
            # Display compliance issues from governance_data JSON first
            compliance_issues_for_run = record_governance_analysis.get("compliance_issues", [])
            
            if compliance_issues_for_run:
                st.markdown("**Compliance Issues:**")
                for issue_idx, issue in enumerate(compliance_issues_for_run, 1):
                    st.markdown(f"{issue_idx}. {issue}")
            else:
                st.markdown("**Compliance Issues:** ✅ None detected")
else:
    st.info("No historical governance records available")

# Footer
st.markdown("---")
st.caption("💡 Tip: Governance analysis is performed by the LLMGovernanceAgent after all other pipeline stages complete.")
