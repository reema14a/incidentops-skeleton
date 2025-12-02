"""
Reusable Chart Components

Provides reusable chart rendering functions for Streamlit dashboards.
Handles severity breakdown, category distribution, and timeline visualizations.
"""

import streamlit as st
from typing import Dict, List, Any
from collections import defaultdict

st.markdown("""
<style>

    /* Reduce padding inside expanders */
    .streamlit-expanderContent {
        padding-top: 0.25rem !important;
        padding-bottom: 0.5rem !important;
    }

    /* Compact tabs: smaller height and tighter spacing */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.4rem;
        margin-bottom: 0.2rem;
    }

    .stTabs [data-baseweb="tab"] {
        padding: 0.2rem 0.6rem !important;
        font-size: 0.85rem !important;
    }

    /* Reduce chart container padding */
    .stPlotlyChart, .stAltairChart, .stVegaLiteChart, .element-container {
        padding-top: 0rem !important;
        padding-bottom: 0rem !important;
        margin-top: -0.5rem !important;
        margin-bottom: -0.5rem !important;
    }

</style>
""", unsafe_allow_html=True)


def render_severity_chart(severity_data: Dict[str, int]) -> None:
    """
    Render severity breakdown chart with detailed breakdown.
    
    Args:
        severity_data: Dictionary mapping severity levels to counts
    """
    if not severity_data:
        st.info("No severity data available")
        return
    
    # Display as bar chart
    st.bar_chart(severity_data)
    
    # Display detailed breakdown
    with st.expander("View Severity Details"):
        severity_col1, severity_col2 = st.columns(2)
        
        with severity_col1:
            st.markdown("**Severity Counts:**")
            for severity, count in sorted(severity_data.items()):
                severity_label = severity.capitalize()
                if severity.lower() == 'high' or severity.lower() == 'critical':
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


def render_category_chart(category_data: Dict[str, int]) -> None:
    """
    Render category distribution chart with detailed breakdown.
    
    Args:
        category_data: Dictionary mapping categories to counts
    """
    if not category_data:
        st.info("No category data available")
        return
    
    # Display as bar chart
    st.bar_chart(category_data)
    
    # Display detailed breakdown
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


def render_timeline_chart(timeline_data: List[Dict[str, Any]]) -> None:
    """
    Render incident timeline chart with execution history.
    
    Args:
        timeline_data: List of timeline records with date, time, and incident counts
    """
    if not timeline_data:
        st.info("No timeline data available (timestamps may be missing)")
        return
    
    # Prepare data for line chart
    timeline_dict = {item['date']: item['incidents'] for item in timeline_data}
    
    # Display as line chart
    st.line_chart(timeline_dict)
    
    # Display detailed timeline
    with st.expander("View Timeline Details"):
        st.markdown("**Execution History:**")
        
        for item in reversed(timeline_data[-10:]):  # Show last 10 executions
            st.write(f"• {item['date']} {item['time']}: {item['incidents']} incidents")
        
        if len(timeline_data) > 10:
            st.caption(f"Showing most recent 10 of {len(timeline_data)} executions")

def render_risk_trend_chart(risk_trend_data):
    """Render risk trend over time (uses numeric mapping)."""
    if not risk_trend_data:
        st.info("No risk trend data available. Run more pipeline executions.")
        return

    # Map risk → numeric
    risk_values = {
        'low': 1,
        'medium': 2,
        'high': 3,
        'critical': 4
    }

    risk_chart_data = {}
    for record in risk_trend_data:
        label = f"{record['date']} {record['time']}"
        risk_chart_data[label] = risk_values.get(record['risk'].lower(), 0)

    # Chart
    st.line_chart(risk_chart_data, height=180)


    # Detail expander
    with st.expander("View Risk Trend Details"):
        for record in reversed(risk_trend_data[-10:]):
            level = record['risk'].capitalize()
            st.write(f"• Run #{record['run_id']} ({record['date']} {record['time']}): {level}")

def render_compliance_trend_chart(compliance_trend_data):
    """Render compliance trend (issue counts over time)."""
    if not compliance_trend_data:
        st.info("No compliance trend data available.")
        return

    compliance_chart_data = {}
    for record in compliance_trend_data:
        label = f"{record['date']} {record['time']}"
        compliance_chart_data[label] = record["issue_count"]

    # Chart
    st.line_chart(compliance_chart_data, height=180)

    # Details
    with st.expander("View Compliance Trend Details"):
        for record in reversed(compliance_trend_data[-10:]):
            icon = "⚠️" if record["issue_count"] > 0 else "✅"
            st.write(f"• {record['date']} {record['time']} — {icon} {record['issue_count']} issue(s)")
