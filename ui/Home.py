"""
Dashboard - Clean, Unified, Submission-Ready

Sections:
• Summary (success cards)
• Insight Highlights (info cards)
• Tarot Preview
• Governance Analytics (info cards)
• Key Observations (interpreting governance patterns)
• Historical Distributions (Escalation, Severity, Category)
"""

import sys
from pathlib import Path
import streamlit as st
from typing import List, Dict, Any
from collections import defaultdict

# Ensure project root on sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Apply global theme
from ui.theme_loader import apply_global_theme, close_sidebar_wrapper
apply_global_theme()

# DB utilities
from db.db_util import (
    get_dashboard_metrics,
    get_pipeline_runs,
    get_severity_distribution,
    get_category_distribution,
    get_timeline_data,
    get_resolution_priority_stats,
    get_compliance_stats,
    get_risk_trend,
    get_escalation_text_counts
)
from utils.insights_loader import get_latest_insights
from utils.formatters import format_timestamp

# Tarot preview
from ui.components.tarot_preview import render_tarot_preview

from config.settings_loader import get_settings
settings = get_settings()

# ---------------------------------------------------------------------------
# PAGE HEADER
# ---------------------------------------------------------------------------

col_title, col_refresh, col_interval = st.columns([6, 1, 1])

with col_title:
    st.title("📊 Dashboards")
    st.markdown("A high-level overview of system health and incident activity.")

with col_refresh:
    st.write("")
    if st.button("🔄 Refresh", use_container_width=True, key="header_refresh_btn"):
        st.rerun()

with col_interval:
    st.write("")
    interval = st.selectbox(
        "Auto-refresh",
        options=[0, 10, 30, 60, 300],
        format_func=lambda x: "Off" if x == 0 else f"{x}s",
        key="auto_refresh_interval",
        label_visibility="collapsed"
    )

# Auto-refresh
if interval > 0:
    import time
    now = time.time()

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = now

    if now - st.session_state.last_refresh >= interval:
        st.session_state.last_refresh = now
        st.rerun()

    remaining = interval - int(now - st.session_state.last_refresh)
    st.info(f"⏱ Auto-refresh in {remaining}s")

st.markdown("---")

# ---------------------------------------------------------------------------
# LOAD DATA
# ---------------------------------------------------------------------------

metrics = get_dashboard_metrics()

if metrics["total_executions"] == 0:
    st.warning("⚠️ No pipeline execution history found.")
    st.markdown("""
    **To get started:**
    1. Go to **Pipeline Runner**
    2. Run the pipeline using log input
    3. Return here to view insights
    """)
    st.stop()

severity_data = get_severity_distribution()
category_data = get_category_distribution()
timeline_data = get_timeline_data()

# ---------------------------------------------------------------------------
# 1️⃣ SUMMARY (success cards)
# ---------------------------------------------------------------------------

st.subheader("📈 Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.success(f"**Total Executions:** {metrics['total_executions']}")

with col2:
    st.success(f"**Total Incidents:** {metrics['total_incidents']}")

with col3:
    st.success(f"**Avg Incidents/Run:** {metrics['avg_incidents_per_run']:.1f}")

with col4:
    st.success(f"**Last Execution:** {format_timestamp(metrics['last_execution_timestamp'])}")

st.markdown("---")

# ---------------------------------------------------------------------------
# 2️⃣ INSIGHT HIGHLIGHTS (info cards)
# ---------------------------------------------------------------------------

st.subheader("💡 Insight Highlights")

most_common_sev = max(severity_data.items(), key=lambda x: x[1])[0] if severity_data else "N/A"
most_common_cat = max(category_data.items(), key=lambda x: x[1])[0] if category_data else "N/A"

# Peak day
peak_day = "N/A"
if timeline_data:
    day_counts = defaultdict(int)
    for item in timeline_data:
        day_counts[item["date"]] += item["incidents"]
    if day_counts:
        peak_day = max(day_counts.items(), key=lambda x: x[1])[0]

# Avg priority
priority_stats = get_resolution_priority_stats()
avg_priority = priority_stats["avg_priority"] if priority_stats["avg_priority"] is not None else "N/A"

colA, colB = st.columns(2)

with colA:
    st.info(f"**🔥 Most Common Severity:** {most_common_sev.capitalize()}")
    st.info(f"**📂 Most Common Category:** {most_common_cat.capitalize()}")

with colB:
    st.info(f"**📅 Peak Incident Day:** {peak_day}")
    st.info(f"**🎯 Avg Resolution Priority:** {avg_priority}")

st.markdown("---")

# ---------------------------------------------------------------------------
# 3️⃣ TAROT PREVIEW
# ---------------------------------------------------------------------------

tarot_enabled = settings.get('tarot', {}).get('enabled', False)

if tarot_enabled:
    st.subheader("🔮 Tarot Preview")

    latest_insights = get_latest_insights()
    shadow_risk = None

    if latest_insights and "insights" in latest_insights:
        shadow_risk = latest_insights["insights"].get("shadow_risk_interpretation")

    render_tarot_preview(shadow_risk)

    st.markdown("---")

# ---------------------------------------------------------------------------
# 4️⃣ GOVERNANCE ANALYTICS (info cards)
# ---------------------------------------------------------------------------

st.subheader("📊 Governance Analytics")

# Load analytics
compliance_stats = get_compliance_stats()
risk_trend = get_risk_trend()
escalation_counts = get_escalation_text_counts()
pipeline_runs = get_pipeline_runs()

# Risk counts
risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
for r in risk_trend:
    lv = r.get("risk", "low").lower()
    if lv in risk_levels:
        risk_levels[lv] += 1

critical_high_count = risk_levels["critical"] + risk_levels["high"]
total_compliance_issues = compliance_stats.get("total_issues", 0)
avg_issues_per_run = compliance_stats.get("avg_issues_per_run", 0.0)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.info(f"**Runs Recorded:** {len(pipeline_runs)}")

with col2:
    st.info(f"**Critical/High Risk:** {critical_high_count}")

with col3:
    st.info(f"**Total Compliance Issues:** {total_compliance_issues}")

with col4:
    st.info(f"**Avg Issues/Run:** {avg_issues_per_run:.1f}")

st.markdown("---")

# ---------------------------------------------------------------------------
# 5️⃣ KEY OBSERVATIONS (interprets analytics)
# ---------------------------------------------------------------------------

st.subheader("🔍 Key Observations")

colL, colR = st.columns(2)

with colL:
    # Most common risk
    if any(risk_levels.values()):
        common_risk = max(risk_levels.items(), key=lambda x: x[1])[0]
        st.markdown(f"**Most Common Risk Level:** {common_risk.capitalize()}")
    else:
        st.markdown("**Most Common Risk Level:** N/A")

    # Compliance issue rate
    if len(pipeline_runs) > 0:
        runs_with_issues = compliance_stats.get("runs_with_issues", 0)
        issue_rate = (runs_with_issues / len(pipeline_runs)) * 100
        st.markdown(f"**Compliance Issue Rate:** {issue_rate:.1f}% of runs")
    else:
        st.markdown("**Compliance Issue Rate:** N/A")

with colR:
    # Most common escalation
    if escalation_counts:
        most_common_esc = max(escalation_counts.items(), key=lambda x: x[1])
        esc_text = most_common_esc[0][:47] + "..." if len(most_common_esc[0]) > 50 else most_common_esc[0]
        st.markdown(f"**Most Common Escalation:** {esc_text} ({most_common_esc[1]} occurrences)")
    else:
        st.markdown("**Most Common Escalation:** N/A")

    # Risk trend direction
    if len(risk_trend) >= 2:
        level_map = {"low": 1, "medium": 2, "high": 3, "critical": 4}
        values = [level_map.get(r["risk"].lower(), 0) for r in risk_trend[-5:]]
        if len(values) >= 2:
            if values[-1] > values[0]:
                st.markdown("**Risk Trend:** 📈 Increasing")
            elif values[-1] < values[0]:
                st.markdown("**Risk Trend:** 📉 Decreasing")
            else:
                st.markdown("**Risk Trend:** ➡️ Stable")
    else:
        st.markdown("**Risk Trend:** N/A")

st.markdown("---")

# ---------------------------------------------------------------------------
# 6️⃣ HISTORICAL DISTRIBUTIONS (charts + summarizations)
# ---------------------------------------------------------------------------

st.subheader("📊 Historical Distributions")

tabs = st.tabs([
    "📢 Escalation Frequency",
    "🔴 Severity Distribution",
    "📂 Category Distribution"
])

# Escalation Frequency
with tabs[0]:
    if escalation_counts:
        st.bar_chart(escalation_counts)
        # summarization
        top_esc = sorted(escalation_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        st.markdown("**Top Escalations:**")
        for e, c in top_esc:
            st.markdown(f"- {e} — {c} occurrence(s)")
        st.caption(f"Total distinct escalation types: {len(escalation_counts)}")
    else:
        st.info("No escalation data available.")

# Severity Distribution
with tabs[1]:
    if severity_data:
        st.bar_chart(severity_data)
        total = sum(severity_data.values())
        st.markdown("**Severity summary:**")
        for sev, cnt in sorted(severity_data.items(), key=lambda x: x[1], reverse=True):
            pct = (cnt / total * 100) if total > 0 else 0
            st.markdown(f"- {sev.capitalize()}: {cnt} ({pct:.1f}%)")
        st.caption(f"Total incidents summarized: {total}")
    else:
        st.info("No severity data available.")

# Category Distribution
with tabs[2]:
    if category_data:
        st.bar_chart(category_data)
        top_cats = sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:5]
        st.markdown("**Top categories:**")
        for c, cnt in top_cats:
            st.markdown(f"- {c.capitalize()}: {cnt}")
        st.caption(f"Total distinct categories: {len(category_data)}")
    else:
        st.info("No category distribution available.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Auto-refresh caption (restored)
# ---------------------------------------------------------------------------

if interval > 0:
    st.caption("Auto-refresh is ON — charts will update when new runs are recorded.")
else:
    st.caption("Enable auto-refresh to update charts automatically when new runs are recorded.")

st.markdown("---")

# ---------------------------------------------------------------------------
# Footer captions (tip + Kiro)
# ---------------------------------------------------------------------------

st.caption("💡 Tip: Dashboard summarizes system-wide historical behavior. For per-run compliance & decisions, see Governance. For LLM insights, see Incident Intelligence.")
st.caption("✨ Powered by Kiro: End-to-end AI-assisted Incident Intelligence and Governance.")

# Close sidebar wrapper
close_sidebar_wrapper()
