"""
Governance Page

Displays risk scoring, escalation decisions, and compliance analysis from the MOST RECENT pipeline execution.
Historical tab now contains ONLY:
• Governance history table
• Per-run expanders
(no charts, no analytics, no trends)
"""

import streamlit as st
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from utils.formatters import format_timestamp

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import DB utilities
from db import db_util


# ------------------------------
# Helper wrappers
# ------------------------------
def safe_call(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default


# ------------------------------
# DB accessors
# ------------------------------
def get_governance_history(limit=None):
    return safe_call(db_util.get_governance_history, limit, default=[])

def get_pipeline_runs(limit=None):
    return safe_call(db_util.get_pipeline_runs, limit, default=[])

def get_audit_summary(run_id):
    return safe_call(db_util.get_audit_summary, run_id, default={})

# ------------------------------
# Latest governance loader
# ------------------------------
def get_latest_governance_data() -> Dict[str, Any]:

    governance_history = get_governance_history(limit=1)
    if not governance_history:
        return {}

    latest = governance_history[0]

    pipeline_runs = get_pipeline_runs(limit=1)
    if not pipeline_runs:
        return {}

    latest_run = pipeline_runs[0]

    # Parse JSON
    gov_json = {}
    if latest.get("governance_data"):
        try:
            gov_json = json.loads(latest["governance_data"])
        except:
            gov_json = {}

    governance_analysis = {
        "risk": latest.get("risk", "unknown"),
        "escalation_category": latest.get("escalation_category", "N/A"),
        "escalation": gov_json.get("escalation", "N/A"),
        "compliance_issues": gov_json.get("compliance_issues", []),
        "commentary": gov_json.get("commentary", latest.get("commentary", "No commentary available")),
        "extra_metadata": gov_json.get("extra_metadata"),
        "additional_context": gov_json.get("additional_context")
    }

    return {
        'execution_timestamp': latest.get('timestamp', 'N/A'),
        'total_incidents': latest_run.get('alerts_count', 0),
        'governance_analysis': governance_analysis,
        'run_id': latest.get('run_id')
    }


# ------------------------------
# Risk display helpers
# ------------------------------
def get_risk_emoji(risk_level: str) -> str:
    risk = (risk_level or "").lower()
    return {
        "critical": "🔴",
        "high": "🟠",
        "medium": "🟡",
        "low": "🟢",
    }.get(risk, "⚪")


# ------------------------------
# Render Page
# ------------------------------
def render_page():

    # ------------------------------
    # Load latest governance
    # ------------------------------
    governance_data = get_latest_governance_data()

    if not governance_data:
        st.title("⚖️ Governance")
        st.warning("No governance analysis found.")
        st.stop()

    ts = governance_data.get("execution_timestamp", "N/A")
    governance_analysis = governance_data.get("governance_analysis", {})

    # ------------------------------
    # Header
    # ------------------------------
    col_title, col_meta = st.columns([5, 2])

    with col_title:
        st.title("⚖️ Governance")
        st.markdown("Governance results and compliance decisions from the most recent pipeline execution.")

    with col_meta:
        st.caption(f"Last Execution: {format_timestamp(ts)}")
        st.caption(f"Pipeline Run ID: #{governance_data.get('run_id', 'N/A')}")

    st.markdown("---")

    # ------------------------------
    # SUMMARY SECTION
    # ------------------------------
    st.markdown("### 📊 Summary")

    risk_level = governance_analysis.get("risk", "unknown")
    risk_emoji = get_risk_emoji(risk_level)
    compliance_issues = governance_analysis.get("compliance_issues", [])

    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🔥 **Total Incidents:** {governance_data.get('total_incidents', 0)}")
    with col2:
        st.success(f"📢 **Escalation:** {governance_analysis.get('escalation_category', 'N/A')}")

    col3, col4 = st.columns(2)
    with col3:
        st.success(f"⚠️ **Risk Level:** {risk_emoji}{risk_level.capitalize()}")
    with col4:
        st.success(f"🛡 **Compliance Issues:** {len(compliance_issues)}")

    st.markdown("---")

    # ------------------------------
    # TABS
    # ------------------------------
    overview_tab, history_tab = st.tabs(["📋 Overview", "📜 Historical"])

    # ------------------------------
    # OVERVIEW TAB — Single-run details
    # ------------------------------
    with overview_tab:

        # RISK
        st.subheader("🎯 Risk Assessment")

        if risk_level.lower() == "critical":
            st.error(f"{risk_emoji} **Risk Level: CRITICAL**")
            st.markdown("⚠️ Immediate attention required.")
        elif risk_level.lower() == "high":
            st.warning(f"{risk_emoji} **Risk Level: HIGH**")
            st.markdown("⚠️ Elevated risk – prompt action recommended.")
        elif risk_level.lower() == "medium":
            st.info(f"{risk_emoji} **Risk Level: Medium**")
            st.markdown("ℹ️ Moderate risk – monitor closely.")
        else:
            st.success(f"{risk_emoji} **Risk Level: Low**")
            st.markdown("✅ System within acceptable parameters.")

        st.markdown("---")

        # ESCALATION
        st.subheader("📢 Escalation Decision")

        st.markdown(f"**Escalation Category:** {governance_analysis.get('escalation_category', 'N/A')}")
        st.markdown(f"**Recommended Action:** {governance_analysis.get('escalation', 'N/A')}")

        st.markdown("---")

        # COMPLIANCE
        st.subheader("📋 Compliance Analysis")

        if compliance_issues:
            st.warning(f"⚠️ {len(compliance_issues)} compliance issue(s) identified")
            for i, issue in enumerate(compliance_issues, 1):
                st.markdown(f"{i}. {issue}")
        else:
            st.success("✅ No compliance issues detected.")

        st.markdown("---")

        # COMMENTARY
        st.subheader("💬 Governance Commentary")
        st.markdown(governance_analysis.get("commentary", "No commentary available"))
        st.markdown("---")

        # RAW JSON
        with st.expander("🔍 View Full Governance Data", expanded=False):
            st.json(governance_analysis)

        # AUDIT SUMMARY
        run_id = governance_data.get("run_id")
        if run_id:
            with st.expander("📝 View Audit Summary", expanded=False):
                try:
                    row = get_audit_summary(run_id)
                    if row:
                        audit_data = {
                            'status': row['status'],
                            'timestamp': format_timestamp(row['timestamp']),
                            'count': row['count']
                        }
                        

                        # Include full JSON data if available
                        if row['audit_data']:
                            try:
                                audit_json = json.loads(row['audit_data'])
                                audit_data['full_audit'] = audit_json
                            except json.JSONDecodeError:
                                pass
                        
                        st.json(audit_data)
                except Exception as e:
                    st.error(f"Error loading audit summary: {e}")

    # ------------------------------
    # HISTORY TAB — Simple table + expanders
    # ------------------------------
    with history_tab:

        st.subheader("📜 Governance History")

        history = get_governance_history()
        if not history:
            st.info("No historical governance records available.")
            st.stop()

        # Build table
        table = []
        for rec in history:
            try:
                clean = json.loads((rec.get("governance_data") or "").strip())
            except:
                clean = {}

            table.append({
                "Run ID": f"#{rec.get('run_id')}",
                "Timestamp": format_timestamp(rec.get("timestamp", "N/A")),
                "Risk": f"{get_risk_emoji(rec.get('risk'))} {rec.get('risk').capitalize()}",
                "Escalation": rec.get("escalation_category", "N/A"),
                "Compliance": len(clean.get("compliance_issues", []))
            })

        df = pd.DataFrame(table)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.markdown("---")

        # Detailed expanders
        st.subheader("🔍 Detailed Run Analysis")

        for rec in history:
            try:
                clean = json.loads((rec.get("governance_data") or "").strip())
            except:
                clean = {}

            risk = rec.get("risk", "unknown")
            run_id = rec.get("run_id")

            with st.expander(f"Run #{run_id} — {format_timestamp(rec.get('timestamp'))} — {get_risk_emoji(risk)} {risk.capitalize()}"):
                st.markdown("**Risk Level:**")
                st.write(f"{get_risk_emoji(risk)} {risk.capitalize()}")

                st.markdown("**Escalation:**")
                st.write(rec.get("escalation_category", "N/A"))

                st.markdown("**Escalation Details:**")
                st.write(clean.get("escalation", "N/A"))

                st.markdown("**Commentary:**")
                st.write(clean.get("commentary", "No commentary available"))

                st.markdown("**Compliance Issues:**")
                issues = clean.get("compliance_issues", [])
                if issues:
                    for i, issue in enumerate(issues, 1):
                        st.markdown(f"{i}. {issue}")
                else:
                    st.success("None detected.")

                with st.expander("📄 Full JSON"):
                    st.json(clean)

    st.markdown("---")
    st.caption("✨ Powered by Kiro: Governance analysis is generated using AI after pipeline execution.")


# Run
if __name__ == "__main__":
    render_page()
