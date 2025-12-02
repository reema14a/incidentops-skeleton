"""
Home - Dashboard 2.0

High-level overview of system health:
• KPIs
• Insight Highlights
• Tarot Preview
• Quick Navigation
• Preview Cards
• Severity / Category / Timeline charts
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

# DB utilities
from db.db_util import (
    get_dashboard_metrics,
    get_pipeline_runs,
    get_severity_distribution,
    get_category_distribution,
    get_timeline_data,
    get_resolution_priority_stats
)
from utils.insights_loader import get_latest_insights
from utils.formatters import format_timestamp

# Chart components
# from ui.components.charts import (
#     render_severity_chart,
#     render_category_chart,
#     render_timeline_chart
# )
from ui.components.tarot_preview import render_tarot_preview
from ui.components.cards import (
    render_mini_severity_card,
    render_mini_categories_card,
    render_mini_timeline_card
)

from config.settings_loader import get_settings
settings = get_settings()

# ---------------------------------------------------------------------------
# Header Row 
# ---------------------------------------------------------------------------

col_title, col_refresh, col_interval = st.columns([6, 1, 1])

with col_title:
    st.title("📊 Dashboards")
    st.markdown("A high-level overview of system health and incident activity.")

# Put the controls into small centered containers so they align vertically
with col_refresh:
    # small spacer to help vertical alignment (avoids label wrapping)
    st.write("") 
    # Use a container to reduce vertical stretch
    with st.container():
        # Render a compact Refresh button; rerun on click
        if st.button("🔄 Refresh", use_container_width=True, key="header_refresh_btn"):
            st.rerun()

with col_interval:
    st.write("")  # spacing for vertical alignment
    with st.container():
        # Keep the same variable name you already use across the file
        interval = st.selectbox(
            "Auto-refresh",
            options=[0, 10, 30, 60, 300],
            format_func=lambda x: "Off" if x == 0 else f"{x}s",
            key="auto_refresh_interval",
            label_visibility="collapsed"
        )


# Auto-refresh mechanism
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
# Load Data
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

# def get_recent_severity_trend(timeline_data, n=5):
#     """Return list of severities for last n runs (derived from severity dist per run)."""
#     recent = timeline_data[-n:] if len(timeline_data) >= n else timeline_data
#     # We need severity for each run -> fallback to category count heuristics
#     # Home page is fine showing severity category inferred from incidents.
#     trend = []
#     for r in recent:
#         incidents = r["incidents"]
#         if incidents == 0:
#             trend.append("none")
#         elif incidents < 3:
#             trend.append("low")
#         elif incidents < 6:
#             trend.append("medium")
#         elif incidents < 10:
#             trend.append("high")
#         else:
#             trend.append("critical")
#     return trend


# def get_top_categories(category_data, top_n=3):
#     if not category_data:
#         return []
#     sorted_items = sorted(category_data.items(), key=lambda x: x[1], reverse=True)
#     return [c for c, _ in sorted_items[:top_n]]


# def get_last5_incident_counts(timeline_data):
#     if not timeline_data:
#         return []
#     return [r["incidents"] for r in timeline_data[-5:]]

# ---------------------------------------------------------------------------
# KPI Summary Row
# ---------------------------------------------------------------------------
st.subheader("📈 Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Executions", metrics["total_executions"])

with col2:
    st.metric("Total Incidents", metrics["total_incidents"])

with col3:
    st.metric("Avg Incidents/Run", f"{metrics['avg_incidents_per_run']:.1f}")

with col4:
    last_exec = metrics["last_execution_timestamp"]
    st.metric("Last Execution", format_timestamp(last_exec))

st.markdown("---")


# ---------------------------------------------------------------------------
# Insight Highlights (info cards)
# ---------------------------------------------------------------------------
st.subheader("💡 Insight Highlights")

# Calculate insights from data
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


# Render as cards
ic1, ic2 = st.columns(2)
with ic1:
    st.info(f"**🔥 Most Common Severity:** {most_common_sev.capitalize()}")
    st.info(f"**📂 Most Common Category:** {most_common_cat.capitalize()}")

with ic2:
    st.info(f"**📅 Peak Incident Day:** {peak_day}")
    st.info(f"**🎯 Avg Resolution Priority:** {avg_priority}")

st.markdown("---")

# ---------------------------------------------------------------------------
# TAROT PREVIEW SECTION
# ---------------------------------------------------------------------------
tarot_enabled = settings.get('tarot', {}).get('enabled', False)

if tarot_enabled:

  st.subheader("🔮 Tarot Preview")

  latest_insights = get_latest_insights()
  shadow_risk = None

  if latest_insights and "insights" in latest_insights:
      shadow_risk = latest_insights["insights"].get("shadow_risk_interpretation")

  render_tarot_preview(shadow_risk)
# else:
#   st.caption("🔮 Tarot Insights are disabled in settings.")

st.markdown("---")


# ---------------------------------------------------------
# Compute Snapshot Data (SAFE — does not break your code)
# ---------------------------------------------------------

# Last 5 runs (reverse chronological)
runs = timeline_data[-5:] if timeline_data else []

# 🔥 Severity trend for last 5 runs
# Each severity is the most common severity in that run's aggregated data
severity_trend_last_5 = []
if runs:
    for r in runs:
        # severity_data is global aggregate, so fallback to overall distribution
        # but you do NOT have per-run severity distribution in DB
        # so we default to most_common_sev (as discussed earlier)
        severity_trend_last_5.append(most_common_sev.capitalize())
else:
    severity_trend_last_5 = ["N/A"] * 5


# 🗂 Top 3 categories
top_3_categories = (
    sorted(category_data.items(), key=lambda x: x[1], reverse=True)[:3]
    if category_data else []
)
top_3_categories = [c[0].capitalize() for c in top_3_categories]


# 📅 Last 5 incident counts
incident_counts_last_5 = [r["incidents"] for r in runs] if runs else []

# -------------------------------------------
# QUICK SNAPSHOTS — Option A1 using cards.py
# -------------------------------------------

st.markdown("## 📌 Quick Snapshots")
st.markdown("")

# 🔥 Recent Severity Trend
st.markdown("### 🔥 Recent Severity Trend")
render_mini_severity_card(severity_trend_last_5)
st.markdown("---")

# 🗂 Top Categories
st.markdown("### 🗂 Top Categories")
render_mini_categories_card(top_3_categories)
st.markdown("---")

# 📅 Last 5 Runs
st.markdown("### 📅 Last 5 Runs")
render_mini_timeline_card(incident_counts_last_5)
st.markdown("---")



# # ---------------------------------------------------------------------------
# # CHARTS SECTION
# # ---------------------------------------------------------------------------
# st.subheader("📊 Trends & Distributions")

# tabs = st.tabs([
#     "🔴 Severity",
#     "📂 Categories",
#     "📅 Timeline"
# ])

# with tabs[0]:
#     render_severity_chart(severity_data)

# with tabs[1]:
#     render_category_chart(category_data)

# with tabs[2]:
#     render_timeline_chart(timeline_data)

# st.markdown("---")
# if interval > 0:
#     st.caption("Auto-refresh is ON — charts will update when new runs are recorded.")
# else:
#     st.caption("Enable auto-refresh to update charts automatically when new runs are recorded.")

