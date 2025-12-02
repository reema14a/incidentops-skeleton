"""
Governance Page

Displays risk scoring, escalation decisions, and compliance analysis from pipeline executions.
Redesigned with Summary Card, Overview tab, and Historical tab layout.
"""

import streamlit as st
import sys
import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from utils.formatters import format_timestamp

# Add project root to Python path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Import database utilities
from db import db_util

def safe_call(fn, *args, default=None, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return default

def get_governance_history(limit=None):
    return safe_call(
        db_util.get_governance_history,
        limit,
        default=[]
    )

def get_pipeline_runs(limit=None):
    return safe_call(
        db_util.get_pipeline_runs,
        limit,
        default=[]
    )

def get_risk_trend(limit=20):
    return safe_call(
        db_util.get_risk_trend,
        limit=limit,
        default=[]
    )

def get_severity_distribution():
    return safe_call(
        db_util.get_severity_distribution,
        default={}
    )

def get_compliance_stats():
    return safe_call(
        db_util.get_compliance_stats,
        default={}
    )

def get_compliance_trend():
    return safe_call(
        db_util.get_compliance_trend,
        default={}
    )

def get_escalation_text_counts():
    return safe_call(
        db_util.get_escalation_text_counts,
        default=[]
    )

def get_category_distribution():
    return safe_call(
        db_util.get_category_distribution,
        default={}
    )


def get_latest_governance_data() -> Dict[str, Any]:
    """
    Extract the most recent governance analysis from the database.
    
    Returns:
        Dict: Latest governance analysis data or empty dict
    """
    # Get the most recent governance analysis from the database
    governance_history = get_governance_history(limit=1)
    # st.json(governance_history)
    if not governance_history:
        return {}
    
    latest = governance_history[0]
    
    # Get the associated pipeline run details
    pipeline_runs = get_pipeline_runs(limit=1)
    
    if not pipeline_runs:
        return {}
    
    latest_run = pipeline_runs[0]
    
    # Parse governance_data JSON if available
    governance_json = {}
    if latest.get("governance_data"):
        try:
            governance_json = json.loads(latest["governance_data"])
        except json.JSONDecodeError:
            governance_json = {}

    # Build normalized governance_analysis
    governance_analysis = {
        "risk": latest.get("risk", "unknown"),                        # ALWAYS from column
        "escalation_category": latest.get("escalation_category", "N/A"),  # ALWAYS from column
        "escalation": governance_json.get("escalation", "N/A"),      # Full text from JSON
        "compliance_issues": governance_json.get("compliance_issues", []),
        "commentary": governance_json.get("commentary", latest.get("commentary", "No commentary available")),
        # More optional fields
        "extra_metadata": governance_json.get("extra_metadata"),
        "additional_context": governance_json.get("additional_context")
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


def render_page():

    # Get latest governance data from database
    governance_data = get_latest_governance_data()

    ts = governance_data.get("execution_timestamp", "N/A")

    # Page configuration
    # st.title("⚖️ Governance")
    # st.markdown("Risk level, escalation decisions, and compliance analysis from pipeline executions.")
    # st.markdown("---")

    col_title, col_meta = st.columns([5, 2])

    with col_title:
        st.title("⚖️ Governance")
        st.markdown(
            " "
            "Governance results and compliance decisions from the most recent pipeline execution."
        )

    with col_meta:
        # Add an empty line to push the caption downward into alignment
        st.caption(f"Last Execution: {format_timestamp(ts)}")
        st.caption(f"Pipeline Run ID: #{governance_data.get('run_id', 'N/A')}")
        

    st.markdown("---")

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

    # ============================================================================
    # SUMMARY CARD - Always visible at top
    # ============================================================================
    # First row: Run metadata
    # col_name, col_details = st.columns([5, 1])
    
    # with col_name:
    st.markdown("### 📊 Summary")

    # with col_details:
    #     with st.expander("", expanded=False):
    #         st.json(governance_analysis)

    risk_level = governance_analysis.get('risk', 'unknown')
    risk_emoji = get_risk_emoji(risk_level)
    compliance_issues = governance_analysis.get("compliance_issues", [])
    compliance_count = len(compliance_issues)

    # First row: Run metadata
    col1, col2 = st.columns(2)

    with col1:
        st.info(f"**🔥 Total Incidents:** {governance_data.get('total_incidents', 0)}")

    with col2:
        st.info(f"**📢 Escalation:** {governance_analysis.get('escalation_category', 'N/A')}")
    

    col3, col4 = st.columns(2)

    with col3:
        st.info(f"**⚠️ Risk Level:** {get_risk_emoji(risk_level)}{risk_level.capitalize()}")

    with col4:
        st.info(f"**🛡 Compliance Issues:** {compliance_count}")

    

    st.markdown("---")

    # ============================================================================
    # TABBED INTERFACE - Overview and Historical
    # ============================================================================
    overview_tab, historical_tab = st.tabs(["📋 Overview", "📈 Historical"])

    # ============================================================================
    # OVERVIEW TAB - Current run details
    # ============================================================================
    with overview_tab:
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
        
        st.markdown(f"**Escalation Category:** {governance_analysis.get('escalation_category', 'N/A')}")
        escalation_full = governance_analysis.get('escalation', 'N/A')
        st.markdown(f"**Recommended Action:** {escalation_full}")
        
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

    # ============================================================================
    # HISTORICAL TAB - DB analytics
    # ============================================================================
    with historical_tab:
        st.subheader("📈 Governance Analytics")
        
        # Get all governance history from database
        all_governance = get_governance_history()
        all_pipeline_runs = get_pipeline_runs()
        
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
        compliance_stats = get_compliance_stats()
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
        
        st.markdown("---")
        
        # Key Observations Summary
        st.subheader("🔍 Key Observations")
        
        key_obs_col1, key_obs_col2 = st.columns(2)
        
        with key_obs_col1:
            # Most common risk level
            if any(risk_counts.values()):
                most_common_risk = max(
                    [(k, v) for k, v in risk_counts.items() if k != 'unknown' and v > 0],
                    key=lambda x: x[1],
                    default=('unknown', 0)
                )
                if most_common_risk[1] > 0:
                    st.markdown(f"**Most Common Risk Level:** {get_risk_emoji(most_common_risk[0])} {most_common_risk[0].capitalize()} ({most_common_risk[1]} runs)")
                else:
                    st.markdown("**Most Common Risk Level:** N/A")
            else:
                st.markdown("**Most Common Risk Level:** N/A")
            
            # Compliance issue rate
            if len(all_pipeline_runs) > 0:
                runs_with_issues = compliance_stats.get('runs_with_issues', 0)
                issue_rate = (runs_with_issues / len(all_pipeline_runs)) * 100
                st.markdown(f"**Compliance Issue Rate:** {issue_rate:.1f}% of runs")
            else:
                st.markdown("**Compliance Issue Rate:** N/A")
        
        with key_obs_col2:
            # Most common escalation
            # Check if function exists (for Streamlit hot reload compatibility)
            if hasattr(db_util, 'get_escalation_text_counts'):
                escalation_counts = db_util.get_escalation_text_counts()
            # else:
            #     # Fallback: manually query escalation counts
            #     try:
            #         with db_util.get_connection() as conn:
            #             cursor = conn.cursor()
            #             cursor.execute("""
            #                 SELECT escalation, COUNT(*) as count
            #                 FROM governance_analysis
            #                 WHERE escalation IS NOT NULL AND escalation != ''
            #                 GROUP BY escalation
            #                 ORDER BY count DESC
            #             """)
            #             rows = cursor.fetchall()
            #             escalation_counts = {row['escalation']: row['count'] for row in rows}
            #     except Exception:
            #         escalation_counts = {}
            
            if escalation_counts:
                most_common_escalation = max(escalation_counts.items(), key=lambda x: x[1])
                # Truncate long escalation text
                escalation_text = most_common_escalation[0]
                if len(escalation_text) > 50:
                    escalation_text = escalation_text[:47] + "..."
                st.markdown(f"**Most Common Escalation:** {escalation_text} ({most_common_escalation[1]} runs)")
            else:
                st.markdown("**Most Common Escalation:** N/A")
            
            # Risk trend direction
            risk_trend_data = get_risk_trend()
            if len(risk_trend_data) >= 2:
                # Map risk levels to numeric values
                risk_values = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                recent_risks = [risk_values.get(r['risk'].lower(), 0) for r in risk_trend_data[-5:]]
                
                if len(recent_risks) >= 2:
                    avg_recent = sum(recent_risks) / len(recent_risks)
                    avg_older = sum([risk_values.get(r['risk'].lower(), 0) for r in risk_trend_data[-10:-5]]) / max(len(risk_trend_data[-10:-5]), 1)
                    
                    if avg_recent > avg_older + 0.3:
                        st.markdown("**Risk Trend:** 📈 Increasing")
                    elif avg_recent < avg_older - 0.3:
                        st.markdown("**Risk Trend:** 📉 Decreasing")
                    else:
                        st.markdown("**Risk Trend:** ➡️ Stable")
                else:
                    st.markdown("**Risk Trend:** N/A")
            else:
                st.markdown("**Risk Trend:** N/A")
        
        st.markdown("---")
        
        # Trend Charts Section
        st.subheader("📊 Trend Analysis")
        
        # Create tabs for different trend views
        trend_tab1, trend_tab2, trend_tab3, trend_tab4, trend_tab5 = st.tabs([
            "🎯 Risk Trend",
            "📋 Compliance Trend",
            "📢 Escalation Frequency",
            "🔴 Severity Distribution",
            "📂 Category Distribution"
        ])
        
        # Tab 1: Risk Trend Chart
        with trend_tab1:
            risk_trend_data = get_risk_trend()
            
            if risk_trend_data:
                # Map risk levels to numeric values for charting
                risk_values = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
                
                # Prepare data for line chart
                risk_chart_data = {}
                for record in risk_trend_data:
                    date_label = f"{record['date']} {record['time']}"
                    risk_chart_data[date_label] = risk_values.get(record['risk'].lower(), 0)
                
                st.line_chart(risk_chart_data)
                
                # Display legend
                st.caption("Risk Levels: 1=Low, 2=Medium, 3=High, 4=Critical")
                
                # Show detailed breakdown
                with st.expander("View Risk Trend Details"):
                    for record in reversed(risk_trend_data[-10:]):
                        risk_emoji_trend = get_risk_emoji(record['risk'])
                        st.write(f"• Run #{record['run_id']} ({record['date']} {record['time']}): {risk_emoji_trend} {record['risk'].capitalize()}")
                    
                    if len(risk_trend_data) > 10:
                        st.caption(f"Showing most recent 10 of {len(risk_trend_data)} records")
            else:
                st.info("No risk trend data available")
        
        # Tab 2: Compliance Trend Chart
        with trend_tab2:
            compliance_trend_data = get_compliance_trend()
            
            if compliance_trend_data:
                # Prepare data for line chart
                compliance_chart_data = {}
                for record in compliance_trend_data:
                    date_label = f"{record['date']} {record['time']}"
                    compliance_chart_data[date_label] = record['issue_count']
                
                st.line_chart(compliance_chart_data)
                
                # Show detailed breakdown
                with st.expander("View Compliance Trend Details"):
                    for record in reversed(compliance_trend_data[-10:]):
                        icon = "✅" if record['issue_count'] == 0 else "⚠️"
                        st.write(f"• Run #{record['run_id']} ({record['date']} {record['time']}): {icon} {record['issue_count']} issue(s)")
                    
                    if len(compliance_trend_data) > 10:
                        st.caption(f"Showing most recent 10 of {len(compliance_trend_data)} records")
            else:
                st.info("No compliance trend data available")
        
        # Tab 3: Escalation Frequency Chart
        with trend_tab3:
            # Check if function exists (for Streamlit hot reload compatibility)
            if hasattr(db_util, 'get_escalation_text_counts'):
                escalation_counts = get_escalation_text_counts()
            # else:
            #     # Fallback: manually query escalation counts
            #     try:
            #         with db_util.get_connection() as conn:
            #             cursor = conn.cursor()
            #             cursor.execute("""
            #                 SELECT escalation, COUNT(*) as count
            #                 FROM governance_analysis
            #                 WHERE escalation IS NOT NULL AND escalation != ''
            #                 GROUP BY escalation
            #                 ORDER BY count DESC
            #             """)
            #             rows = cursor.fetchall()
            #             escalation_counts = {row['escalation']: row['count'] for row in rows}
            #     except Exception:
            #         escalation_counts = {}
            
            if escalation_counts:
                # Display as bar chart
                st.bar_chart(escalation_counts)
                
                # Show detailed breakdown
                with st.expander("View Escalation Details"):
                    st.markdown("**Escalation Recommendations:**")
                    for escalation_text, count in sorted(escalation_counts.items(), key=lambda x: x[1], reverse=True):
                        st.write(f"• {escalation_text}: {count} occurrence(s)")
            else:
                st.info("No escalation data available")
        
        # Tab 4: Severity Distribution Chart
        with trend_tab4:
            severity_data = get_severity_distribution()
            
            if severity_data:
                # Display as bar chart
                st.bar_chart(severity_data)
                
                # Show detailed breakdown
                with st.expander("View Severity Details"):
                    severity_col1, severity_col2 = st.columns(2)
                    
                    with severity_col1:
                        st.markdown("**Severity Counts:**")
                        for severity, count in sorted(severity_data.items()):
                            severity_label = severity.capitalize()
                            if severity.lower() in ['high', 'critical']:
                                st.error(f"🔴 {severity_label}: {count}")
                            elif severity.lower() == 'medium':
                                st.warning(f"🟡 {severity_label}: {count}")
                            else:
                                st.success(f"🟢 {severity_label}: {count}")
                    
                    with severity_col2:
                        st.markdown("**Percentage Distribution:**")
                        total = sum(severity_data.values())
                        for severity, count in sorted(severity_data.items()):
                            percentage = (count / total * 100) if total > 0 else 0
                            st.write(f"{severity.capitalize()}: {percentage:.1f}%")
            else:
                st.info("No severity data available")
        
        # Tab 5: Category Distribution Chart
        with trend_tab5:
            category_data = get_category_distribution()
            
            if category_data:
                # Display as bar chart
                st.bar_chart(category_data)
                
                # Show detailed breakdown
                with st.expander("View Category Details"):
                    category_col1, category_col2 = st.columns(2)
                    
                    with category_col1:
                        st.markdown("**Category Counts:**")
                        for category, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
                            st.write(f"• {category.capitalize()}: {count}")
                    
                    with category_col2:
                        st.markdown("**Percentage Distribution:**")
                        total = sum(category_data.values())
                        for category, count in sorted(category_data.items(), key=lambda x: x[1], reverse=True):
                            percentage = (count / total * 100) if total > 0 else 0
                            st.write(f"{category.capitalize()}: {percentage:.1f}%")
            else:
                st.info("No category data available")
        
        st.markdown("---")
        
        # Governance History Table with collapsible per-run details
        st.subheader("📜 Governance History")
        
        if all_governance:
            st.markdown(f"Showing {len(all_governance)} governance analysis record(s)")
            
            # Create a table view of governance history
            table_data = []
            for record in all_governance:
                # Parse governance_data JSON for this record
                raw_json = record.get("governance_data", "") or ""
                clean_json = raw_json.strip().replace("\n", " ").replace("\r", " ")

                try:
                    record_governance_analysis = json.loads(clean_json)
                except Exception:
                    record_governance_analysis = {}

                risk_level_hist = record.get('risk', 'unknown')
                escalation_hist = record.get('escalation_category', 'N/A')
                
                # Count compliance issues
                compliance_issues_for_run = record_governance_analysis.get("compliance_issues", [])
                issue_count = len(compliance_issues_for_run)
                
                table_data.append({
                    'Run ID': f"#{record.get('run_id')}",
                    'Timestamp': format_timestamp(record.get('timestamp', 'N/A')),
                    'Risk': f"{get_risk_emoji(risk_level_hist)} {risk_level_hist.capitalize()}",
                    'Escalation': escalation_hist,
                    'Compliance Issues': issue_count
                })
            
            # Display as dataframe
            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # Per-run JSON expanders (collapsible history)
            st.subheader("🔍 Detailed Run Analysis")
            
            for idx, record in enumerate(all_governance):
                # Parse governance_data JSON for this record
                raw_json = record.get("governance_data", "") or ""
                clean_json = raw_json.strip().replace("\n", " ").replace("\r", " ")

                try:
                    record_governance_analysis = json.loads(clean_json)
                except Exception:
                    record_governance_analysis = {}

                risk_level_detail = record.get('risk', 'unknown')
                
                with st.expander(
                    f"Run #{record.get('run_id')} - {format_timestamp(record.get('timestamp', 'N/A'))} - "
                    f"{get_risk_emoji(risk_level_detail)} {risk_level_detail.capitalize()}",
                    expanded=False
                ):
                    # Display normalized governance fields (JSON only)
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**Risk Level:**")
                        st.markdown(f"{get_risk_emoji(risk_level_detail)} {risk_level_detail.capitalize()}")

                        st.markdown("**Escalation:**")
                        st.write(record.get("escalation_category", "N/A"))

                    with col2:
                        st.markdown("**Execution Time:**")
                        st.write(format_timestamp(record.get("timestamp", "N/A")))

                        st.markdown("**Run ID:**")
                        st.write(f"#{record.get('run_id')}")
                    
                    # Display escalation details
                    st.markdown("**Escalation Details:**")
                    commentary_detail = record_governance_analysis.get('escalation', 'N/A')
                    st.markdown(commentary_detail)

                    # Display commentary
                    st.markdown("**Commentary:**")
                    commentary_detail = record_governance_analysis.get('commentary', 'No commentary available')
                    st.markdown(commentary_detail)
                    
                    # Display compliance issues from governance_data JSON first
                    compliance_issues_for_run = record_governance_analysis.get("compliance_issues", [])
                    
                    if compliance_issues_for_run:
                        st.markdown("**Compliance Issues:**")
                        for issue_idx, issue in enumerate(compliance_issues_for_run, 1):
                            st.markdown(f"{issue_idx}. {issue}")
                    else:
                        st.markdown("**Compliance Issues:** ✅ None detected")
                    
                    # Full JSON expander
                    st.markdown("---")
                    with st.expander("📄 View Full JSON Data"):
                        st.json(record_governance_analysis)
        else:
            st.info("No historical governance records available")

    # Footer
    st.markdown("---")
    st.caption("💡 Tip: Governance analysis is performed by the LLMGovernanceAgent after all other pipeline stages complete.")

if __name__ == "__main__":
    render_page()
